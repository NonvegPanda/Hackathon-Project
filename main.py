from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length
from flask_bcrypt import Bcrypt
import google.generativeai as genai
from flask_migrate import Migrate

# Initialize Flask App
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = '8080'

# Initialize Extensions
database = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
migrate = Migrate(app, database)

genai.configure(api_key="AIzaSyC-PJMrcaRgwL_bxSX7FkREzJu5kcVqlEg")

# User Model
class User(UserMixin, database.Model):
    id = database.Column(database.Integer, primary_key=True)
    username = database.Column(database.String(150), unique=True, nullable=False)
    password = database.Column(database.String(150), nullable=False)
    role = database.Column(database.String(20), nullable=False, default='student')  # Default role: student

# Forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=150)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=150)])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=150)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=150)])
    submit = SubmitField('Register')

# Flask-Login User Loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash("Username already exists. Choose another.", "danger")
            return redirect(url_for('register'))
        
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        role = 'teacher' if form.username.data.startswith('teacher') else 'student'
        new_user = User(username=form.username.data, password=hashed_password, role=role)
        
        database.session.add(new_user)
        database.session.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            session['role'] = user.role  # Store role in session
            flash("Login successful!", "success")
            
            return redirect(url_for('teacher' if user.role == 'teacher' else 'index'))
        flash("Invalid username or password.", "danger")
    
    return render_template('login.html', form=form)

# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('role', None)  
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


tasks = ['Buy groceries', 'Complete coding tutorial', 'Walk the dog']
shop_items = {
    'Sword of Strength': {'cost': 5},
    'Shield of Defense': {'cost': 3},
    'Potion of Health': {'cost': 2}
}


@app.route('/')
@login_required
def index():
    if session.get('role') != 'student':
        flash("Access denied. Students only.", "danger")
        return redirect(url_for('teacher'))

    score = session.get('score', 0)
    inventory = session.get('inventory', [])
    return render_template('index.html', tasks=tasks, score=score, inventory=inventory, shop_items=shop_items)

@app.route('/teacher')
@login_required
def teacher():
    if session.get('role') != 'teacher':
        flash("Access denied. Teachers only.", "danger")
        return redirect(url_for('index'))
    
    score = session.get('score', 0)
    return render_template('teacher.html', tasks=tasks, score=score)

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/add', methods=['POST'])
@login_required
def add_task():
    if session.get('role') != 'teacher':
        flash("Access denied.", "danger")
        return redirect(url_for('teacher'))
    
    new_task = request.form.get('newTask')
    if new_task:
        tasks.append(new_task)
    return redirect(url_for('teacher'))


@app.route('/complete', methods=['POST'])

def complete():

    
    completed_tasks = request.form.getlist('taskCheckbox')
    score = session.get('score', 0)

    for i in completed_tasks:
        if int(i) - 1 < len(tasks):
            tasks[int(i)-1] += " - Completed"
            score += 1

    session['score'] = score
    return redirect(url_for('index'))

# Get Score
@app.route('/get_score')
def get_score():
    score = session.get('score')
    return jsonify({'score': score})

# Buy Item
@app.route('/buy_item', methods=['POST'])
@login_required
def buy_item():
    item_name = request.form.get('item_name')
    item_cost = shop_items.get(item_name, {}).get('cost', 0)
    score = session.get('score', 0)

    if score >= item_cost:
        score -= item_cost
        session['score'] = score
        inventory = session.get('inventory', [])
        if item_name not in inventory:
            inventory.append(item_name)
            session['inventory'] = inventory

    return redirect(url_for('index'))

# Adventure Game
@app.route('/game', methods=['GET', 'POST'])
def game():
    score = session.get('score', 0)
    inventory = session.get('inventory', [])

    character_description = f"The character starts out as a weak individual, but with the accumulated Nerves from tasks, they have gained strength. Their current task score is {score}. "

    if score >= 10:
        character_description += "The character is now wearing golden armor due to their heroic deeds. "
    elif score >= 5:
        character_description += "The character has a strong shield, providing extra defense. "
    else:
        character_description += "The character is still building strength, but shows great potential. "

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
        prompt = f"{character_description} Continue the adventure based on this choice: {choice}. Make the story short and reflect the character's growth based on their achievements. Don't mention the score directly, but let their actions and items shape the story. Give 4 options always and list the options again at the last line."
    else:
        prompt = f"{character_description} The character embarks on their journey, facing challenges ahead. What will they do next? Give 4 options always and list the options again at the last."

    response = chat_session.send_message(prompt)
    text = response.text

   
    lines = text.strip().split("\n")
    options = [line.strip("- ") for line in lines[-4:]] 
    return render_template('game.html', text=text, score=score, inventory=inventory, options=options)



def create_tables():
    with app.app_context():
        database.create_all()

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
