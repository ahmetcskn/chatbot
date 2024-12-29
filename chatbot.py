import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import json
from textblob import TextBlob
import sqlite3
from datetime import datetime

class SmartBot:
    def __init__(self):
        # Bağlam yönetimi için
        self.context = []
        self.memory_size = 5
        
        # Veritabanı bağlantısı
        self.conn = sqlite3.connect('chatbot.db')
        self.cursor = self.conn.cursor()
        
        # Tüm tabloları oluştur
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations
            (user_input TEXT, bot_response TEXT, sentiment TEXT, timestamp DATETIME)
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS learned_responses
            (question TEXT, answer TEXT, created_at DATETIME)
        ''')
        
        # Temel yanıtlar için yeni tablo
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS base_responses
            (category TEXT, question TEXT, answer TEXT)
        ''')
        
        # Eğer base_responses boşsa, temel yanıtları ekle
        self.cursor.execute('SELECT COUNT(*) FROM base_responses')
        if self.cursor.fetchone()[0] == 0:
            self._initialize_base_responses()
        
        # Tüm yanıtları yükle
        self._load_responses()

    def _initialize_base_responses(self):
        """Temel yanıtları veritabanına ekle"""
        base_data = [
            ("selamlaşma", "merhaba nasılsın", "İyiyim, teşekkür ederim! Siz nasılsınız?"),
            ("selamlaşma", "selam", "Selam! Nasıl yardımcı olabilirim?"),
            ("kişisel", "adın ne", "Benim adım AD-1!"),
            # ... diğer yanıtlar ...
        ]
        
        self.cursor.executemany('''
            INSERT INTO base_responses (category, question, answer)
            VALUES (?, ?, ?)
        ''', base_data)
        self.conn.commit()

    def _load_responses(self):
        """Tüm yanıtları veritabanından yükle"""
        # Base responses'ı yükle
        self.cursor.execute('SELECT question, answer FROM base_responses')
        base_pairs = self.cursor.fetchall()
        
        # Learned responses'ı yükle
        self.cursor.execute('SELECT question, answer FROM learned_responses')
        learned_pairs = self.cursor.fetchall()
        
        # Training data'yı oluştur
        self.training_data = {}
        for question, answer in base_pairs + learned_pairs:
            self.training_data[question] = answer
        
        # Vektörleri güncelle
        self.vectorizer = TfidfVectorizer()
        self.X = self.vectorizer.fit_transform(list(self.training_data.keys()))

    def get_response(self, user_input):
        # Bağlamı güncelle
        self.context.append(user_input)
        if len(self.context) > self.memory_size:
            self.context.pop(0)
        
        # Duygu analizi yap
        sentiment = self.analyze_sentiment(user_input)
        
        # Yanıt oluştur
        user_vector = self.vectorizer.transform([user_input])
        similarities = cosine_similarity(user_vector, self.X)
        most_similar = np.argmax(similarities)
        
        if similarities[0][most_similar] < 0.1:
            response = "Üzgünüm, sizi tam olarak anlayamadım. Başka türlü ifade edebilir misiniz?"
        else:
            response = list(self.training_data.values())[most_similar]
        
        # Konuşmayı veritabanına kaydet
        self.save_conversation(user_input, response, sentiment)
        
        return response

    def analyze_sentiment(self, text):
        analysis = TextBlob(text)
        if analysis.sentiment.polarity > 0:
            return "positive"
        elif analysis.sentiment.polarity < 0:
            return "negative"
        return "neutral"

    def save_conversation(self, user_input, response, sentiment):
        timestamp = datetime.now()
        self.cursor.execute('''
            INSERT INTO conversations (user_input, bot_response, sentiment, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (user_input, response, sentiment, timestamp))
        self.conn.commit()

    def learn_from_feedback(self, user_input, correct_response):
        """Kullanıcı geri bildirimine göre öğrenme ve veritabanına kaydetme"""
        # Yeni cevabı training_data'ya ekle
        self.training_data[user_input] = correct_response
        
        # Veritabanına kaydet
        timestamp = datetime.now()
        self.cursor.execute('''
            INSERT INTO learned_responses (question, answer, created_at)
            VALUES (?, ?, ?)
        ''', (user_input, correct_response, timestamp))
        self.conn.commit()
        
        # Vektörleri güncelle
        self.X = self.vectorizer.fit_transform(list(self.training_data.keys()))

    def get_conversation_history(self):
        """Son konuşmaları getir"""
        self.cursor.execute('''
            SELECT * FROM conversations 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        return self.cursor.fetchall()

    def get_learned_responses(self):
        """Öğrenilmiş tüm cevapları getir"""
        self.cursor.execute('''
            SELECT question, answer, created_at 
            FROM learned_responses 
            ORDER BY created_at DESC
        ''')
        return self.cursor.fetchall()

    def __del__(self):
        """Veritabanı bağlantısını kapat"""
        self.conn.close()