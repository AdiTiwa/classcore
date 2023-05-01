from wtforms import Form, StringField, PasswordField, Field
from wtforms.validators import DataRequired, Email, Length, EqualTo
from wtforms.widgets import TextArea

class TagListField(Field):
    widget = TextArea()

    def _value(self):
        if self.data:
            return u', '.join(self.data)
        else:
            return u' '
    
    def process_formdata(self, valueList):
        if valueList:
            self.data = [x.strip() for x in valueList[0].split(',')]
        else:
            self.data = []

class RegistrationForm(Form):
    username = StringField('Username', [Length(min=4, max=25)])
    email = StringField('Email Address', [Length(min=6, max=35), Email()])
    password = PasswordField('Password', [
        DataRequired(),
        EqualTo('confirm', message="Passwords must match.")
    ])
    confirm = PasswordField("Repeat Password")

class LoginForm(Form):
    email = StringField('Email Address', [Length(min=6, max=35), Email()])
    password = PasswordField('Password', [DataRequired()])

class CreateDocument(Form):
    name = StringField('Document Name', [DataRequired()])
    documentText = StringField("Document Text", [DataRequired()], widget=TextArea())

class CreateClass(Form):
    name = StringField("Class Name", [DataRequired()])
    description = StringField("Class Description", [DataRequired()], widget=TextArea())