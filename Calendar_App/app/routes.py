from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for, flash
import os
import json
import uuid
import sys
from flask import Flask
from .initialization import initialize_and_persist_vectorstore
import llama_index.core.chat_engine.types
import time
if not hasattr(sys, 'getdefaultencoding') or sys.getdefaultencoding() != 'utf-8':
    import importlib
    importlib.reload(sys)
    sys.setdefaultencoding('utf-8')
import win32com.client
import json
from llama_index.core import SimpleDirectoryReader, Settings, SummaryIndex
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
import pythoncom  # Ajout de l'importation de pythoncom
import re


app = Flask(__name__)
app.secret_key = 'MySecretKey'
main = Blueprint('main', __name__)

users = {"ismail": "MDP123", "mounia": "MDP123", "yousef": "MDP123", "salma": "MDP123"}

# Set your paths
PDF_PATH = 'splited_emails'
PERSIST_DIR = './storage'

# Initialize chat engine
chat_engine = initialize_and_persist_vectorstore(PDF_PATH, PERSIST_DIR)


@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['username'] = username
            flash('Vous êtes maintenant connecté.', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect', 'danger')
    return render_template('login.html')

def get_user_categories(username):
    user_categories_file = f'user_categories_{username}.json'
    if os.path.exists(user_categories_file):
        with open(user_categories_file, 'r', encoding='utf-8') as f:
            user_categories = json.load(f)
    else:
        user_categories = []
    return user_categories

@main.route('/')
def home():
    username = session.get('username')
    if not username:
        flash('Vous devez être connecté pour accéder à cette page.', 'danger')
        return redirect(url_for('main.login'))
    categories = get_user_categories(username)
    return render_template('index.html', categories=categories)

@main.route('/chatbot')
def chatbot():
    username = session.get('username')
    if not username:
        flash('Vous devez être connecté pour accéder à cette page.', 'danger')
        return redirect(url_for('main.login'))
    categories = get_user_categories(username)
    return render_template('chatbot.html',categories=categories)

@main.route('/send_message', methods=['POST'])
def send_message():
    message = request.form['message']
    print("Received message:", message)
    
    # Obtenir la réponse du moteur de chat
    response = chat_engine.chat(message)
    print("Type of response:", type(response))
    print(response)
    
    # Adapter pour extraire les parties sérialisables de l'objet AgentChatResponse
    if isinstance(response, llama_index.core.chat_engine.types.AgentChatResponse):
        response_data = {
            'response': response.response,  # Assurez-vous que 'response' est l'attribut correct à extraire
        }
    else:
        response_data = str(response)
    
    # Retourner la réponse comme JSON
    return jsonify(response_data)

@main.route('/calendar')
def calendar():
    username = session.get('username')
    if not username:
        flash('Vous devez être connecté pour accéder à cette page.', 'danger')
        return redirect(url_for('main.login'))
    categories = get_user_categories(username)
    return render_template('calendar.html',categories=categories)

@main.route('/refresh_events', methods=['POST'])
def refresh_events():
    username = session.get('username')
    if not username:
        flash('Vous devez être connecté pour actualiser les événements.', 'danger')
        return redirect(url_for('main.login'))

    user_categories = get_user_categories(username)
    category_list_str = ", ".join(user_categories)

    def extract_and_save_emails_attachments(count, save_path):
        pythoncom.CoInitialize()  # Initialiser COM
        try:
            outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
            inbox = outlook.GetDefaultFolder(6)
            messages = inbox.Items
            messages.Sort("[ReceivedTime]", True)
            with open(os.path.join(save_path, 'emails_with_attachments.txt'), 'w', encoding='utf-8') as email_file:
                for i in range(count):
                    message = messages[i]
                    try:
                        email_file.write(f"Subject: {message.Subject}\n")
                        email_file.write(f"Sender: {message.Sender}\n")
                        email_file.write(f"Received Time: {message.ReceivedTime}\n")
                        email_file.write(f"Body: {message.Body}\n\n")
                    except Exception as ex:
                        print("Error saving email or attachments:", ex)
        finally:
            pythoncom.CoUninitialize()  # Désinitialiser COM

    save_path = 'emails'
    os.makedirs(save_path, exist_ok=True)
    extract_and_save_emails_attachments(40, save_path)

    def remove_links(content):
        url_pattern = re.compile(
            r'(?<!mailto:)(http|https|ftp|ftps)://[^\s/$.?#].[^\s]*|www\.[^\s]+|<https?://[^\s>]+>'
        )
        return url_pattern.sub('', content)

    def split_emails(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        content = remove_links(content)
        
        emails = content.split("Subject:")
        if emails[0].strip() == "":
            emails = emails[1:]
        emails = ["Subject:" + email for email in emails]
        
        os.makedirs('C', exist_ok=True)
        
        for idx, email in enumerate(emails):
            with open(f'splited_emails/email_{idx+1}.txt', 'w', encoding='utf-8') as email_file:
                email_file.write(email)
                
    split_emails(os.path.join(save_path, 'emails_with_attachments.txt'))

    input_dir = 'splited_emails'
    os.environ["OPENAI_API_KEY"] = "sk-proj-vHbGimMSVyxKKCd0KKVXT3BlbkFJ7jH1F0rVIQAvJPokrAN7"
    Settings.llm = OpenAI(model="gpt-4o", api_key="sk-proj-vHbGimMSVyxKKCd0KKVXT3BlbkFJ7jH1F0rVIQAvJPokrAN7", max_tokens=4000)
    Settings.embed_model = OpenAIEmbedding(model_name="text-embedding-3-large", max_tokens=4000, api_key="sk-proj-vHbGimMSVyxKKCd0KKVXT3BlbkFJ7jH1F0rVIQAvJPokrAN7")
    documents1 = SimpleDirectoryReader(input_dir=input_dir).load_data()
    index1 = SummaryIndex.from_documents(documents=documents1)
    query_engine = index1.as_query_engine()
    query = "Extract all events (examens, rattrapages, soutenance, rencontre, conférence, événement, réuinion, entretien, invitation ... Etc) from emails json format with title, start(time with hour, format example: 2024-06-19T13:00:00), end (time with hour, format example: 2024-06-19T14:00:00), description(short one), and location. avoid duplication. with no markdown"
    events = query_engine.query(query).response
    print(events)
    
    try:
        events = json.loads(events)
    except json.JSONDecodeError:
        print("Erreur de décodage JSON")
        events = []

    output_file = 'events.json'
    
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=4)
    
    category_query = f"Categorize the emails into JSON format with the following fields: category (one of: {category_list_str}), subject(well formulated in French), summary(in french, it must be short have a sense and well structured). return only mails with content. with no markdown"
    category = query_engine.query(category_query).response
    print(category)
    try:
        category = json.loads(category)
    except json.JSONDecodeError:
        print("Erreur de décodage JSON")
        category = []

    category_output = 'emails_category.json'
    with open(category_output, 'w', encoding='utf-8') as f:
        json.dump(category, f, ensure_ascii=False, indent=4)

    return jsonify({"success": True})


@main.route('/events')
def get_events():
    events_file_path = os.path.join(os.path.dirname(__file__), '../events.json')
    with open(events_file_path, 'r', encoding='utf-8') as f:
        events = json.load(f)
    return jsonify(events)


@main.route('/add_event', methods=['POST'])
def add_event():
    new_event = request.json
    new_event['id'] = str(uuid.uuid4())
    events_file_path = os.path.join(os.path.dirname(__file__), '../events.json')
    with open(events_file_path, 'r', encoding='utf-8') as f:
        events = json.load(f)
    events.append(new_event)
    with open(events_file_path, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=4)
    return jsonify({"success": True})

@main.route('/delete_event', methods=['POST'])
def delete_event():
    event_title_to_delete = request.json['title']
    events_file_path = os.path.join(os.path.dirname(__file__), '../events.json')
    with open(events_file_path, 'r', encoding='utf-8') as f:
        events = json.load(f)
    events = [event for event in events if event['title'] != event_title_to_delete]
    with open(events_file_path, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=4)
    return jsonify({"success": True})

@main.route('/category/<category_name>')
def category(category_name):
    username = session.get('username')
    if not username:
        flash('Vous devez être connecté pour accéder à cette page.', 'danger')
        return redirect(url_for('main.login'))
        
    categories = get_user_categories(username)
    with open(f'emails_category.json', 'r', encoding='utf-8') as f:
        emails_category = json.load(f)
    
    filtered_emails = [email for email in emails_category if email.get('category', 'Autres') == category_name]
    return render_template('category.html', categories=categories, category_name=category_name, emails=filtered_emails)

@main.route('/add_category', methods=['POST'])
def add_category():
    category_name = request.form.get('category-name')
    if not category_name:
        flash('Le nom de la catégorie est requis.', 'danger')
        return redirect(url_for('main.home'))

    username = session.get('username')
    if not username:
        flash('Vous devez être connecté pour ajouter une catégorie.', 'danger')
        return redirect(url_for('main.login'))

    user_categories_file = f'user_categories_{username}.json'
    if os.path.exists(user_categories_file):
        with open(user_categories_file, 'r', encoding='utf-8') as f:
            user_categories = json.load(f)
    else:
        user_categories = []

    user_categories.append(category_name)
    with open(user_categories_file, 'w', encoding='utf-8') as f:
        json.dump(user_categories, f, ensure_ascii=False, indent=4)

    flash('Catégorie ajoutée avec succès.', 'success')
    return redirect(url_for('main.home'))

app.register_blueprint(main)
