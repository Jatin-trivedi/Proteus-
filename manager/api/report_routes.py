import csv
import io
import json
from flask import Blueprint, jsonify, request, send_file
from models import db, Finding, Report
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
    return {"finding_count": len(findings), "findings": findings}


@report_bp.post("")
def create_report():
    data = request.get_json() or {}
    filters = data.get("filters") if isinstance(data.get("filters"), dict) else {}
    report = Report(
        name=data.get("name", "Forensic Report"),
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
        document.setFont("Helvetica-Bold", 16)
        document.drawString(48, y, report.name)
        y -= 24
        document.setFont("Helvetica", 10)
        document.drawString(
            48,
            y,
            f"Type: {report.report_type} | Findings: {report.content.get('finding_count', 0)}",
        )
        y -= 28
        for finding in report.content.get("findings", []):
            for line in (
                f"[{finding['severity'].upper()}] {finding['title']}",
                f"{finding['category']} | Agent: {finding['agent_id']} | Status: {finding['status']}",
                finding["description"],
            ):
                if y < 48:
                    document.showPage()
                    y = height - 48
                document.drawString(48, y, line[:110])
                y -= 14
            y -= 8
        document.save()
        stream.seek(0)
        return send_file(
            stream,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{report.report_id}.pdf",
        )
    if output_format != "csv":
        return jsonify({"error": "format must be json, csv, or pdf"}), 400
    stream = io.StringIO()
    writer = csv.DictWriter(
        stream,
        fieldnames=[
            "finding_id", "agent_id", "severity", "category", "title",
            "description", "status", "created_at",
        ],
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(report.content.get("findings", []))
    return send_file(io.BytesIO(stream.getvalue().encode()), mimetype="text/csv", as_attachment=True, download_name=f"{report.report_id}.csv")
