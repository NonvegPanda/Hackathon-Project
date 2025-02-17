from flask import Flask, render_template, request, redirect, url_for, session
from flask.json import jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin , login_user, LoginManager, login_required, logout_user ,current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length ,ValidationError
from flask_bcrypt import Bcrypt


import google.generativeai as genai

app = Flask(__name__)
app.secret_key = "8080"
  
genai.configure(api_key="AIzaSyC-PJMrcaRgwL_bxSX7FkREzJu5kcVqlEg")


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY']='8080'

database = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, database.Model):
    id = database.Column(database.Integer, primary_key=True)
    username = database.Column(database.String(150), unique=True, nullable=False)
    password = database.Column(database.String(150), nullable=False)
    role = database.Column(database.String(50), nullable=False)  # Add role attribute

class RegisterForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=20)])
    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user = User.query.filter_by(username=username.data).first()
        if existing_user:
            raise ValidationError("Username already exists. Please choose a different one.")

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=20)])
    submit = SubmitField('Login')


tasks = ['Buy groceries', 'Complete coding tutorial', 'Walk the dog']
shop_items = {
    'Sword of Strength': {'cost': 5},
    'Shield of Defense': {'cost': 3},
    'Potion of Health': {'cost': 2}
}

@app.route('/')
def index():
    score = session.get('score', 0)
    inventory = session.get('inventory', [])
    return render_template('index.html', tasks=tasks, score=score, inventory=inventory, shop_items=shop_items)

@app.route('/home')
def home():
    score = session.get('score', 0)
    return render_template('home.html',score=score)

@app.route('/login' ,methods=['GET','POST'] )
def login():
    form=LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('home'))
        
    return render_template('login.html',form=form)



@app.route('/register', methods=['GET','POST'])
def register():
    form=RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        database.session.add(new_user)
        database.session.commit()
        return redirect(url_for('login'))
        
    
    return render_template('register.html',form=form)



@app.route('/teacher')
def teacher():
    score = session.get('score', 0)
    if 'score' in session:
        session['score'] = score
    else:
        session['score'] = 0
    print(score)
    return render_template('teacher.html', tasks=tasks, score=score)
   
    



@app.route('/add', methods=['POST'])
def add_task():
    new_task = request.form.get('newTask')
    if new_task:
        tasks.append(new_task)
    return redirect(url_for('teacher'))

@app.route('/complete', methods=['POST'])
def complete():
    global score  
    score = 0
    completed_tasks = request.form.getlist('taskCheckbox')
    
    for i in completed_tasks:
        if int(i) - 1 < len(tasks):
            tasks[int(i)-1] += " - Completed"
            session['score'] += 1
    return redirect(url_for('teacher'))

@app.route('/get_score')
def get_score():
    score = session.get('score')
    return jsonify({'score': score})

@app.route('/buy_item', methods=['POST'])
def buy_item():
    item_name = request.form.get('item_name')
    item_cost = shop_items.get(item_name, {}).get('cost', 0)
    score = session.get('score', 0)

    # Check if the user has enough score
    if score >= item_cost:
        # Deduct the cost from score
        score -= item_cost
        session['score'] = score

        # Add the item to the inventory
        inventory = session.get('inventory', [])
        if item_name not in inventory:
            inventory.append(item_name)
            session['inventory'] = inventory

    return redirect(url_for('index'))

@app.route('/game', methods=['GET', 'POST'])
def game():
    score = session.get('score', 0)
    inventory = session.get('inventory', [])
    
    # Prepare the description based on score and inventory
    character_description = f"The character starts out as a weak individual, but with the accumulated Nerves from tasks, they have gained strength. Their current task score is {score}. "
    
    # Add description of the character's appearance based on their score
    if score >= 10:
        character_description += "The character is now wearing golden armor due to their heroic deeds. "
    elif score >= 5:
        character_description += "The character has a strong shield, providing extra defense. "
    else:
        character_description += "The character is still building strength, but shows great potential. "
    
    # Add inventory effects
    inventory_effects = []
    for item in inventory:
        if item == "Sword of Strength":
            inventory_effects.append("They wield the Sword of Strength, enhancing their combat abilities.")
        elif item == "Shield of Defense":
            inventory_effects.append("They carry the Shield of Defense, improving their ability to withstand damage.")
        elif item == "Potion of Health":
            inventory_effects.append("They possess a Potion of Health, ready to restore their vitality in battle.")

    if inventory_effects:
        character_description += " ".join(inventory_effects)

    model = genai.GenerativeModel("gemini-pro")
    chat_session = model.start_chat()

    if request.method == 'POST':
        choice = request.form.get('choice', '')
        prompt = f"{character_description} Continue the adventure based on this choice: {choice}. Make the story short and reflect the character's growth based on their achievements. Don't mention the score directly, but let their actions and items shape the story. GIve 4 options always and list the options again at the last line"
    else:
        prompt = f"{character_description} The character embarks on their journey, facing challenges ahead. What will they do next? GIve 4 options always and list the options again at the last "

    response = chat_session.send_message(prompt)
    text = response.text

    return render_template('game.html', text=text, score=score, inventory=inventory)


if __name__ == '__main__':
    app.run(debug=True)

    