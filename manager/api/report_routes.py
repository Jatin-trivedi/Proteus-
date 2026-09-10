import csv
import io
import json
from flask import Blueprint, jsonify, request, send_file
from models import db, Finding, Report, Result, Agent
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

report_bp = Blueprint("report", __name__, url_prefix="/api/v1/report")


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
