import csv
import io
import json
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, send_file
from models import db, Finding, Report, Result, Agent
from middleware.auth import jwt_required
from audit_logger import get_audit_events
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

report_bp = Blueprint("report", __name__, url_prefix="/api/v1/report")


def build_siem_document(filters):
    """Build a JSON-LD security-event document for SIEM ingestion."""
    query = Finding.query
    if filters.get("agent_id"):
        query = query.filter_by(agent_id=filters["agent_id"])
    if filters.get("severity"):
        query = query.filter_by(severity=filters["severity"])

    finding_events = []
    for finding in query.order_by(Finding.created_at.desc()).all():
        finding_data = finding.to_dict()
        finding_events.append({
            "@type": "FindingEvent",
            "event_type": "finding",
            "event_id": finding.finding_id,
            "timestamp": finding_data["created_at"],
            "severity": finding.severity,
            "source": "proteus.manager",
            "message": finding.title,
            "finding": finding_data,
        })

    audit_events = []
    for event in get_audit_events(
        agent_id=filters.get("agent_id"),
        event_type=filters.get("event_type"),
    ):
        audit_events.append({
            "@type": "AuditEvent",
            "event_type": "audit",
            "event_id": f"audit:{event['timestamp']}:{event['event_type']}",
            "timestamp": event["timestamp"],
            "severity": "info",
            "source": "proteus.manager",
            "message": event["event_type"],
            "audit": event,
        })

    events = finding_events + audit_events
    events.sort(key=lambda event: event["timestamp"], reverse=True)
    return {
        "@context": {
            "@vocab": "https://proteus.example/schema/siem#",
            "event_id": "https://schema.org/identifier",
            "timestamp": "https://schema.org/dateCreated",
            "message": "https://schema.org/description",
        },
        "@type": "SecurityEventBundle",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "proteus.manager",
        "filters": filters,
        "event_count": len(events),
        "events": events,
    }


def build_content(filters):
    query = Finding.query
    if filters.get("agent_id"):
        query = query.filter_by(agent_id=filters["agent_id"])
    if filters.get("severity"):
        query = query.filter_by(severity=filters["severity"])
    findings = [finding.to_dict() for finding in query.order_by(Finding.created_at.desc()).all()]

    results = Result.query.order_by(Result.submitted_at.desc()).all()
    results_list = [{
        "result_id": r.result_id,
        "agent_id": r.agent_id,
        "script_id": r.script_id,
        "submitted_at": r.submitted_at.isoformat(),
        "summary": (r.data_encrypted[:80] + "...") if r.data_encrypted else "N/A"
    } for r in results]

    agents = Agent.query.all()
    agents_list = [{
        "agent_id": a.agent_id,
        "hostname": a.hostname or "unknown",
        "os": a.os or "unknown",
        "ip": a.ip or "127.0.0.1"
    } for a in agents]

    return {
        "finding_count": len(findings),
        "findings": findings,
        "result_count": len(results_list),
        "results": results_list,
        "agent_count": len(agents_list),
        "agents": agents_list
    }


@report_bp.post("")
def create_report():
    data = request.get_json() or {}
    filters = data.get("filters") if isinstance(data.get("filters"), dict) else {}
    report = Report(
        name=data.get("name", "Forensic Investigation Report"),
        report_type=data.get("report_type", "full"),
        filters=filters,
        content=build_content(filters),
    )
    db.session.add(report)
    db.session.commit()
    return jsonify(report.to_dict()), 201


@report_bp.get("/list")
def list_reports():
    return jsonify([report.to_dict() for report in Report.query.order_by(Report.created_at.desc()).all()]), 200


@report_bp.get("/<report_id>")
def get_report(report_id):
    report = Report.query.get(report_id)
    if not report:
        return jsonify({"error": "Report not found"}), 404
    return jsonify(report.to_dict()), 200


@report_bp.get("/export/siem")
def export_siem():
    """Export findings and recent audit events as a JSON-LD SIEM bundle."""
    filters = {
        key: request.args[key]
        for key in ("agent_id", "severity", "event_type")
        if request.args.get(key)
    }
    document = json.dumps(build_siem_document(filters), ensure_ascii=False, indent=2)
    return send_file(
        io.BytesIO(document.encode("utf-8")),
        mimetype="application/ld+json",
        as_attachment=True,
        download_name="proteus_siem_events.jsonld",
    )


@report_bp.delete("/<report_id>")
@jwt_required
def delete_report(report_id):
    report = Report.query.get(report_id)
    if not report:
        return jsonify({"error": "Report not found"}), 404
    db.session.delete(report)
    db.session.commit()
    return jsonify({"status": "deleted", "report_id": report_id}), 200


@report_bp.get("/<report_id>/export")
def export_report(report_id):
    report = Report.query.get(report_id)
    if not report:
        return jsonify({"error": "Report not found"}), 404
    output_format = request.args.get("format", "json").lower()
    if output_format == "json":
        return jsonify(report.to_dict()), 200

    if output_format == "pdf":
        stream = io.BytesIO()
        document = canvas.Canvas(stream, pagesize=letter)
        _, height = letter
        y = height - 48

        # Header Title
        document.setFont("Helvetica-Bold", 16)
        document.drawString(48, y, f"PROTEUS // {report.name}")
        y -= 22

        # Subtitle
        document.setFont("Helvetica", 9)
        document.drawString(
            48,
            y,
            f"Case: {report.report_id[:8].upper()} | Type: {report.report_type.upper()} | Generated: {report.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        )
        y -= 26

        # Findings section
        document.setFont("Helvetica-Bold", 12)
        document.drawString(48, y, "1. EXECUTIVE SUMMARY & EVIDENCE TELEMETRY")
        y -= 18

        document.setFont("Helvetica", 9)
        document.drawString(48, y, f"Total Findings Correlated: {report.content.get('finding_count', 0)}")
        y -= 14
        document.drawString(48, y, f"Total Reporting Agents: {report.content.get('agent_count', 0)}")
        y -= 14
        document.drawString(48, y, f"Total Telemetry Artifacts: {report.content.get('result_count', 0)}")
        y -= 24

        findings = report.content.get("findings", [])
        if findings:
            document.setFont("Helvetica-Bold", 11)
            document.drawString(48, y, "2. CORRELATED FINDINGS")
            y -= 18
            for finding in findings:
                document.setFont("Helvetica-Bold", 9)
                document.drawString(48, y, f"[{finding.get('severity', 'MED').upper()}] {finding.get('title', 'Finding')}")
                y -= 13
                document.setFont("Helvetica", 8)
                document.drawString(56, y, f"Category: {finding.get('category')} | Agent: {finding.get('agent_id')}")
                y -= 12
                document.drawString(56, y, str(finding.get('description', ''))[:100])
                y -= 16
                if y < 60:
                    document.showPage()
                    y = height - 48
        else:
            document.setFont("Helvetica-Bold", 11)
            document.drawString(48, y, "2. ACTIVE AGENT TELEMETRY ARTIFACTS")
            y -= 18
            for res in report.content.get("results", [])[:15]:
                document.setFont("Helvetica-Bold", 9)
                document.drawString(48, y, f"Artifact: {res.get('result_id')} (Agent: {res.get('agent_id')})")
                y -= 13
                document.setFont("Helvetica", 8)
                document.drawString(56, y, f"Submitted: {res.get('submitted_at')} | Script: {res.get('script_id')}")
                y -= 12
                document.drawString(56, y, f"Payload: {res.get('summary')}")
                y -= 16
                if y < 60:
                    document.showPage()
                    y = height - 48

        # Footer Signature
        document.setFont("Helvetica-Oblique", 8)
        document.drawString(48, 30, "Proteus Forensic Intelligence Framework — Court-Admissible Evidence Dossier")
        document.save()
        stream.seek(0)
        return send_file(
            stream,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{report.name.lower().replace(' ', '_')}_{report.report_id[:8]}.pdf",
        )

    if output_format == "csv":
        stream = io.StringIO()
        findings = report.content.get("findings", [])
        if findings:
            writer = csv.DictWriter(
                stream,
                fieldnames=[
                    "finding_id", "agent_id", "severity", "category", "title",
                    "description", "status", "created_at",
                ],
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(findings)
        else:
            results_data = report.content.get("results", [])
            writer = csv.DictWriter(
                stream,
                fieldnames=["result_id", "agent_id", "script_id", "submitted_at", "summary"],
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(results_data)

        return send_file(
            io.BytesIO(stream.getvalue().encode()),
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"{report.name.lower().replace(' ', '_')}_{report.report_id[:8]}.csv",
        )

    return jsonify({"error": "format must be json, csv, or pdf"}), 400
