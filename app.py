import secrets
import time

from flask import (
    Flask,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
)

from contacts_model import Archiver, Contact

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
Contact.load_db()


@app.route("/")
def index():
    return redirect("/contacts")


@app.route("/contacts")
def contacts():
    search = request.args.get("q")
    page = int(request.args.get("page", 1))
    rows_only = request.args.get("rows_only") == "true"
    if search:
        contacts_set = Contact.search(search)
    else:
        contacts_set = Contact.all(page)

    template_name = "hv/rows.xml" if rows_only else "hv/index.xml"
    return render_to_response(
        template_name, contacts=contacts_set, page=page, archiver=Archiver.get()
    )


@app.route("/contacts/new", methods=["GET"])
def contacts_get_new():
    return render_to_response("hv/new.xml", contact=Contact())


@app.route("/contacts/new", methods=["POST"])
def contacts_new():
    c = Contact(
        None,
        request.form["first_name"],
        request.form["last_name"],
        request.form["phone"],
        request.form["email"],
    )
    if c.save():
        return render_to_response("hv/form_fields.xml", contact=c, saved=True)
    else:
        return render_to_response("hv/form_fields.xml", contact=c)


@app.route("/contacts/<contact_id>")
def contacts_view(contact_id=0):
    contact = Contact.find(contact_id)
    return render_to_response("hv/show.xml", contact=contact)


@app.route("/contacts/<contact_id>/edit", methods=["GET"])
def contracts_edit_get(contact_id=0):
    contact = Contact.find(contact_id)
    return render_to_response("hv/edit.xml", contact=contact)


@app.route("/contacts/<contact_id>/edit", methods=["POST"])
def contacts_edit_post(contact_id=0):
    print(f"REQUEST: {request.form}")
    contact = Contact.find(contact_id)
    contact.update(
        request.form["first_name"],
        request.form["last_name"],
        request.form["phone"],
        request.form["email"],
    )
    if contact.save():
        return render_to_response("hv/form_fields.xml", contact=contact, saved=True)
    else:
        return render_to_response("hv/form_fields.xml", contact=contact)


@app.route("/contacts/<contact_id>/delete", methods=["post"])
def contacts_delete(contact_id=0):
    contact = Contact.find(contact_id)
    contact.delete()
    return render_to_response("hv/deleted.xml")


@app.route("/contacts", methods=["DELETE"])
def contacts_delete_all():
    contact_ids = list(map(int, request.form.getlist("selected_contact_ids")))
    page = int(request.args.get("page", 1))
    for contact_id in contact_ids:
        contact = Contact.find(contact_id)
        contact.delete()
    flash("Deleted Contacts!")
    contacts_set = Contact.all()
    return render_template(
        "index.html", contacts=contacts_set, page=page, archiver=Archiver.get()
    )


@app.route("/contacts/<contact_id>/email", methods=["GET"])
def contacts_email_get(contact_id=0):
    c = Contact.find(contact_id)
    c.email = request.args.get("email")
    c.validate()
    return c.errors.get("email") or ""


@app.route("/contacts/count")
def contacts_count():
    count = Contact.count()
    return "(" + str(count) + " total Contacts)"


@app.route("/contacts/archive", methods=["POST"])
def start_archive():
    archiver = Archiver.get()
    archiver.run()
    return render_template("archive_ui.html", archiver=archiver)


@app.route("/contacts/archive", methods=["GET"])
def archive_status():
    archiver = Archiver.get()
    return render_template("archive_ui.html", archiver=archiver)


@app.route("/contacts/archive/file", methods=["GET"])
def archive_content():
    manager = Archiver.get()
    return send_file(manager.archive_file(), "archive.json", as_attachment=True)


@app.route("/contacts/archive", methods=["DELETE"])
def reset_archive():
    archiver = Archiver.get()
    archiver.reset()
    return render_template("archive_ui.html", archiver=archiver)


@app.route("/api/v1/contacts", methods=["GET"])
def json_contacts():
    contacts_set = Contact.all()
    contacts_dicts = [c.__dict__ for c in contacts_set]
    return {"contacts": contacts_dicts}


@app.route("/api/v1/contacts", methods=["POST"])
def json_contacts_new():
    c = Contact(
        None,
        request.form.get("first_name"),
        request.form.get("last_name"),
        request.form.get("email"),
    )
    if c.save():
        return c.__dict__
    else:
        return {"errors": c.errors}, 400


@app.route("/api/v1/contacts/<contact_id>", methods=["GET"])
def json_contacts_view(contact_id=0):
    contact = Contact.find(contact_id)
    return contact.__dict__


@app.route("/api/v1/contacts/<contact_id>", methods=["PUT"])
def json_contacts_edit(contact_id):
    c = Contact.find(contact_id)
    c.update(
        request.form["first_name"],
        request.form["last_name"],
        request.form["phone"],
        request.form["email"],
    )
    if c.save():
        return c.__dict__
    else:
        return {"errors": c.errors}, 400


@app.route("/api/v1/contacts/<contact_id>", methods=["DELETE"])
def json_contacts_delete(contact_id=0):
    contact = Contact.find(contact_id)
    contact.delete()
    return jsonify({"success": True})


def render_to_response(template_name, *args, **kwargs):
    content = render_template(template_name, *args, **kwargs)
    response = make_response(content)
    response.headers["Content-Type"] = "application/vnd.hyperview+xml"
    return response
