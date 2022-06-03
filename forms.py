from wtforms import Form,StringField,TextAreaField,PasswordField,validators,IntegerField,SelectField,FileField,SubmitField



class AddForm(Form):
    product_name = StringField("Product Name",[validators.Length(min=3,max=50),validators.DataRequired()])
    product_price = IntegerField("Price",[validators.DataRequired()])
    SIZE = ["XS","S","M","L","XL","XXL"]
    product_size = SelectField("Size",choices=SIZE,default=1)
    file =  FileField("File")
    submit = SubmitField("Upload File")


