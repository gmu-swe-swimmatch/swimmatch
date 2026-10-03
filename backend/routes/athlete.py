"""Swimmer profile CRUD — stubbed for the scaffold."""
from flask import Blueprint, flash, jsonify, redirect, url_for

from backend.models import Swimmer, db

athlete_bp = Blueprint("athlete", __name__, url_prefix="/athlete")


@athlete_bp.get("/api/<int:swimmer_id>")
def get_swimmer(swimmer_id):
    swimmer = db.get_or_404(Swimmer, swimmer_id)
    return jsonify(swimmer.to_dict())


@athlete_bp.post("/<int:swimmer_id>/update")
def update_swimmer(swimmer_id):
    """Handle the profile edit form.

    TODO: validate form fields, parse times like "1:41.80" into seconds,
    upsert SwimmerEventTime rows (SCY), and commit.
    """
    db.get_or_404(Swimmer, swimmer_id)
    flash("Saving profiles isn't wired up yet — this form is a placeholder.", "info")
    return redirect(url_for("pages.profile"))


@athlete_bp.post("/create")
def create_swimmer():
    # TODO: create a Swimmer from submitted form/JSON once accounts exist.
    return jsonify({"error": "Not implemented"}), 501


@athlete_bp.post("/<int:swimmer_id>/delete")
def delete_swimmer(swimmer_id):
    # TODO: delete swimmer (and cascade event times) once accounts exist.
    return jsonify({"error": "Not implemented"}), 501
