import os
from flask import Flask, redirect, render_template, request, jsonify, url_for, session
from firebase_admin import credentials, firestore, initialize_app
from forms import RegistrationForm, LoginForm, CreateDocument, CreateClass

app = Flask(__name__)
app.secret_key = "such_a_secret_eh"


"""

Work Schedule:
45 minutes work 10 minutes of stretching

TODO LIST:
Logged-out Home Page
Document Lists Styling
Base Create Root Site

Create the script for the video,
Include shot list.


"""


cred = credentials.Certificate('key.json')
default_app = initialize_app(cred)
db = firestore.client()
users_ref = db.collection('users')
classes_ref = db.collection('classes')
documents_ref = db.collection('documents')

def refreshSessionClasses(user):
    session["classes"] = [{"name": refClass.get().get("name"), "id": refClass.get().id, "description": refClass.get().get("description"), "documents": [{} for doc in refClass.get().get("documents")]} for refClass in user.get("classes")]

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/user', methods=['GET'])
def read():
    user_id = request.args.get('user_id')

    if not user_id:
        user_id = session["userId"]

    user = users_ref.document(user_id).get()
    userClasses = []
    userClassIDs = []
    for userClass in user.get("classes"):
        userClasses.append(userClass.get().get("name"))
        userClassIDs.append(userClass.id)
    userOwns = []
    for owns in user.get("owns"):
        userOwns.append({"type": owns["type"], "reference": owns["ref"].get().get("name"), "referenceId": owns["ref"].id})
    return render_template("user_view.html", userName=user.get("user"), userDescription=user.get("description"), userClasses=userClasses, userClassIDs=userClassIDs, userOwns=userOwns, isEditable=(not user_id) or (user_id == session["userId"] and session["isLoggedIn"]))

@app.route('/classes', methods=["GET", "POST"])
def classes():
    class_id = request.args.get('class_id')
    document_id = request.args.get('doc_id')

    allClasses = []

    if request.method == 'POST':
        if request.form["submit_button"] == "Enroll in Class":
            new_user = users_ref.document(session["userId"]).get().to_dict()
            new_user["classes"].append(classes_ref.document(class_id))
            users_ref.document(session["userId"]).set(new_user)

            session["userClasses"] = [refClass.get().id for refClass in users_ref.document(session["userId"]).get().get("classes")]

            return redirect(f"/classes?class_id={class_id}")

    if not class_id:
        return render_template("class_list.html", allClasses=[{"name":refClass.get("name"), "id": refClass.id, "description": refClass.get("description")} for refClass in classes_ref.get()])
    else:
        refClass = classes_ref.document(class_id).get()

        if document_id:
            doc_id = request.args.get('doc_id')
            document = documents_ref.document(doc_id).get()
            docAuthors = []
            for author in document.get('authors'):
                docAuthors.append({ "name": author.get().get('user'), "id": author.id })
            return render_template("document_view.html", docName = document.get("name"), docTags=document.get('tags'), docAuthors = docAuthors, docText = document.get('text'), underClass=None)
        else:
            classAuthors = []
            for author in refClass.get("authors"):
                classAuthors.append({ "name": author.get().get("user"), "id": author.id })
            classDocuments = []
            for document in refClass.get("documents"):
                classDocuments.append({ "name": document.get().get("name"), "id": document.id })
            enrolledStudents = []
            for student in refClass.get("students"):
                enrolledStudents.append({ "name": student.get().get("user"), "id": student.id })

            return render_template("class_view.html", classId = class_id, className = refClass.get("name"), classTags=refClass.get("tags"), classAuthors=classAuthors, classDocuments=classDocuments, classDescription= refClass.get("description"), students=enrolledStudents, userEnrolled = class_id in session["userClasses"])

@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        for user in users_ref.get():
            if form.email.data == user.get("email"):
                if form.password.data == user.get("password"):
                    session["userId"] = user.id
                    session["userName"] = user.get('user')
                    session["userClasses"] = [refClass.get().id for refClass in user.get("classes")]
                    session["userClassNames"] = [refClass.get().get("name") for refClass in user.get("classes")]
                    session["userClassDescriptions"] = [refClass.get().get("description") for refClass in user.get("classes")]
                    session["isLoggedIn"] = True
                    return redirect("/")
    return render_template("login.html", form=form)

@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if request.method == "POST" and form.validate():
        registrationValid = True
        for user in users_ref.get():
            if form.email.data == user.get('email') or form.password.data == user.get('password'):
                registrationValid = False
        if registrationValid:
            new_user = users_ref.add({ "classes": [], "description": "Hey! I love learning. I clearly wrote all of this and am not just too lazy to change the default text for this ;)", "email": form.email.data, "owns": {}, "user": form.username.data , "password": form.password.data } )
            session["userId"] = new_user.id
            session["userClasses"] = []
            session["isLoggedIn"] = True
            session["userClassNames"] = [refClass.get().get().get("name") for refClass in user.get("classes")]
            return redirect("/")
    return render_template("register.html", form=form)

@app.route('/logout', methods=["GET", "POST"])
def logout():
    session["userId"] = ""
    session["userClasses"] = []
    session["isLoggedIn"] = False
    return redirect("/")

@app.route('/document', methods=['GET'])
def document():
    doc_id = request.args.get('doc_id')
    document = documents_ref.document(doc_id).get()
    docAuthors = []
    for author in document.get('authors'):
        docAuthors.append({ "name": author.get().get('user'), "id": author.id })
    return render_template("document_view.html", docName = document.get("name"), docTags=document.get('tags'), docAuthors = docAuthors, docText = document.get('text'), underClass=None)

@app.route('/create/document', methods=["GET", "POST"])
def create_document():
    form = CreateDocument()

    if request.method == "POST" and form.validate():
        document_data = { "name": form.name.data, "tags":["HI", "debug"], "text": form.documentText.data, "authors": [users_ref.document(session["userId"]).__copy__()] }
        document_ref = documents_ref.add(document_data)

        new_user = users_ref.document(session["userId"]).get().to_dict()
        new_user["owns"].append({ "type": "document", "ref": document_ref[1].__copy__() })
        users_ref.document(session["userId"]).set(new_user)

        return redirect(f'/document?doc_id={document_ref[1].id}')

    return render_template("create_document.html", form=form)

@app.route('/create/class')
def create_class():
    return "this is the creation page for the classes"

@app.route('/create')
def create():
    return "this is the root create page"

@app.route("/enroll")
def enroll():
    class_id = request.args.get('class_id')

    if not class_id:
        return redirect('/classes')
    else:
        new_user = users_ref.document(session["userId"]).get().to_dict()
        new_user["classes"].append(classes_ref.document(class_id))
        users_ref.document(session["userId"]).set(new_user)

        session["userClasses"] = [refClass.get().id for refClass in users_ref.document(session["userId"]).get().get("classes")]

        return redirect(f"/classes?class_id={class_id}")

port = int(os.environ.get('PORT', 5050))
if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.run(debug=True, threaded=True, port=port)
