from flask import current_app
from flask_mail import Message
from sqlalchemy import select
from app.models.models import User
from app import db

class EmailService:
    @staticmethod
    def send_email_to_winner(winner_id, auction_id, auction_data):
        mail = current_app.extensions.get('mail')
        # query su db postgres per recuperare l'email del vincitore usando winner_id
        query = select(User).where(User.blockChainId == winner_id)
        users_db = db.session.execute(query).scalars().all()
        current_app.logger.info(f"Preparing to send email to {winner_id}")
        try:
            # Crea il messaggio
            # msg = Message(
            #     subject="Ciao dalla mia app Flask!",
            #     recipients=[users_db[0].email] # Inserisci l'email a cui vuoi inviare
            # )

            # # Testo semplice
            # #msg.body = f"Questa è un'email di prova inviata con Flask-Mail e Gmail. Hai vinto l'asta con ID {auction_id} pagando {auction_data.get('winning_amount')}!"

            # # (Opzionale) Testo in formato HTML
            # msg.html = "<h1>HAI VINTO</h1><p>Congratulazioni! Hai vinto l'asta con ID {} pagando {}!</p>".format(auction_id, auction_data.get('high_bid_amount'))

            # # Invia l'email
            # mail.send(msg)
            # Formattiamo il prezzo per renderlo più leggibile (es. 1500.5 -> 1.500,50)
            winning_amount = "{:,.2f}".format(float(auction_data.get('high_bid_amount', 0))).replace(',', 'X').replace('.', ',').replace('X', '.')

            # 1. Modifica l'oggetto per renderlo più accattivante
            msg = Message(
                subject=f"🎉 Hai vinto l'asta #{auction_id} su BuySellChain!",
                recipients=[users_db[0].email] 
            )

            # 2. Testo Semplice (Plain Text) - Fondamentale per i filtri antispam
            msg.body = f"""
                Congratulazioni!

                Siamo felici di comunicarti che la tua offerta è risultata vincente. Ti sei appena aggiudicato l'asta su BuySellChain!

                DETTAGLI DELL'AGGIUDICAZIONE:
                - ID Asta: #{auction_id}
                - Importo Vincente: € {winning_amount}

                Accedi alla tua dashboard su BuySellChain per visualizzare i dettagli completi e procedere con i prossimi step.

                Grazie per aver partecipato,
                Il team di BuySellChain
                """

            # 3. Testo Formattato (HTML) - Quello che vedrà effettivamente l'utente
            msg.html = f"""
            <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                
                <div style="background-color: #10b981; padding: 30px 20px; text-align: center; color: white;">
                    <h1 style="margin: 0; font-size: 28px; letter-spacing: 1px;">🎉 HAI VINTO! 🎉</h1>
                </div>
                
                <div style="padding: 30px 20px; color: #333333; line-height: 1.6; background-color: #ffffff;">
                    <p style="font-size: 16px;">Ciao,</p>
                    <p style="font-size: 16px;">Siamo entusiasti di comunicarti che la tua offerta è risultata la migliore. Ti sei appena aggiudicato un'asta sulla piattaforma <strong>BuySellChain</strong>!</p>
                    
                    <div style="background-color: #f8fafc; padding: 20px; border-left: 5px solid #10b981; margin: 25px 0; border-radius: 4px;">
                        <h3 style="margin-top: 0; color: #1e293b; font-size: 18px;">Dettagli dell'Aggiudicazione</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; color: #64748b; font-weight: bold; width: 40%;">Codice Asta:</td>
                                <td style="padding: 8px 0; color: #0f172a;">#{auction_id}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #64748b; font-weight: bold;">Importo Finale:</td>
                                <td style="padding: 8px 0; color: #10b981; font-weight: bold; font-size: 18px;">€ {winning_amount}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <p style="font-size: 16px;">Il prossimo passo è completare la transazione. Clicca sul pulsante qui sotto per accedere alla tua dashboard e visualizzare tutti i dettagli.</p>
                    
                    <div style="text-align: center; margin: 35px 0;">
                        <a href="http://127.0.0.1:5000/auction/{auction_id}" style="background-color: #10b981; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px; display: inline-block;">Visualizza la tua Asta</a>
                    </div>
                </div>
                
                <div style="background-color: #f1f5f9; padding: 20px; text-align: center; font-size: 13px; color: #64748b; border-top: 1px solid #e2e8f0;">
                    <p style="margin: 0 0 10px 0;">Hai ricevuto questa email perché hai un account attivo su BuySellChain.</p>
                    <p style="margin: 0;">&copy; 2026 BuySellChain. Tutti i diritti riservati.</p>
                </div>
            </div>
            """

            # Invia l'email
            mail.send(msg)
            # Simulazione dell'invio dell'email (sostituisci con la logica reale)
            current_app.logger.info(f"Sending email to winner {winner_id} for auction {auction_id} with data: {auction_data}")
            # Qui potresti integrare un servizio di email reale come SendGrid, Amazon SES, etc.
            return {"success": True}
        except Exception as e:
            current_app.logger.error(f"Error sending email: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def send_email_to_admin():
        mail = current_app.extensions.get('mail')
        try:
            # Simulazione dell'invio dell'email (sostituisci con la logica reale)
            current_app.logger.info("Simulating email sending to admin")
            # 1. Modifica l'oggetto per renderlo più accattivante
            msg = Message(
                subject=f"Notifica regiustrazione come seller su BuySellChain!",
                recipients=["francosalvucci14@gmail.com"] 
            )
            msg.body = f"""
                Ciao Admin,

                Un nuovo utente si è registrato come seller su BuySellChain. 

                Controlla la dashboard per approvare o rifiutare la registrazione.

                Grazie,
                Il team di BuySellChain
                """
            mail.send(msg)
            # Qui potresti integrare un servizio di email reale come SendGrid, Amazon SES, etc.
            return {"success": True}
        except Exception as e:
            current_app.logger.error(f"Error sending email: {str(e)}")
            return {"success": False, "error": str(e)}

