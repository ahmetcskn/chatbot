from chatbot import SmartBot
import time
from datetime import datetime

def print_history(history):
    print("\n=== Son Konuşmalar ===")
    for conv in history:
        user_input, response, sentiment, timestamp = conv
        timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
        print(f"\nTarih: {timestamp.strftime('%Y-%m-%d %H:%M')}")
        print(f"Kullanıcı: {user_input}")
        print(f"AD-1: {response}")
        print(f"Duygu Durumu: {sentiment}")
    print("=====================")

def main():
    bot = SmartBot()
    print("AD-1: Merhaba! Ben AD-1. Seninle sohbet etmekten mutluluk duyarım.")
    print("İpucu: Benimle sohbet edebilir, sorular sorabilirsiniz!")
    print("Özel komutlar:")
    print("- 'geçmiş': Son konuşmaları gösterir")
    print("- 'öğret': Bana yeni bir şey öğretir")
    print("- 'çıkış': Sohbeti sonlandırır")
    
    while True:
        user_input = input("\nSiz: ")
        
        if user_input.lower() == "çıkış":
            print("\nAD-1: Görüşmek üzere! İyi günler!")
            break
            
        elif user_input.lower() == "geçmiş":
            history = bot.get_conversation_history()
            print_history(history)
            continue
            
        elif user_input.lower() == "öğret":
            print("\nAD-1: Bana ne öğretmek istersiniz?")
            question = input("Soru/Durum: ")
            answer = input("Cevap: ")
            bot.learn_from_feedback(question, answer)
            print("AD-1: Teşekkürler! Bunu öğrendim.")
            continue
            
        response = bot.get_response(user_input)
        print("AD-1:", response)

if __name__ == "__main__":
    main() 