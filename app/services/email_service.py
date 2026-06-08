from datetime import datetime

from flask import current_app
from flask_mail import Message
from sqlalchemy import select
from app.models.models import User, BidStatus
from app.services.guile_services import GuileService

class EmailService:

    @staticmethod
    def _parse_bid_timestamp(timestamp_value):
        if not timestamp_value:
            return None
        try:
            clean_timestamp = str(timestamp_value).rstrip("Z")
            return datetime.fromisoformat(clean_timestamp)
        except ValueError:
            return None

    @staticmethod
    def _format_amount(value):
        return "{:,.2f}".format(float(value or 0)).replace(',', 'X').replace('.', ',').replace('X', '.')

    @staticmethod
    def _get_user_email(user_id):
        if not user_id:
            return None

        result = GuileService.GetKV(Class="Users", key=str(user_id))
        if not isinstance(result, dict) or "error" in result:
            return None

        answer = result.get("answer", {})
        if not isinstance(answer, dict):
            return None

        value = answer.get("value")
        if not isinstance(value, dict):
            return None

        try:
            user = User.from_json(value)
            return user.email if user and getattr(user, "email", None) else None
        except Exception:
            return None

    @staticmethod
    def _build_winner_message(auction_id, winning_amount, seller_email):
        return {
            "subject": f"🎉 Hai vinto l'asta #{auction_id} su BuySellChain!",
            "body": f"""
                Congratulazioni!

                Siamo felici di comunicarti che la tua offerta è risultata vincente. Ti sei appena aggiudicato l'asta su BuySellChain!

                DETTAGLI DELL'AGGIUDICAZIONE:
                - ID Asta: #{auction_id}
                - Importo Vincente: € {winning_amount}

                Accedi alla tua dashboard su BuySellChain per visualizzare i dettagli completi e procedere con i prossimi step.

                Grazie per aver partecipato,
                Il team di BuySellChain
                """,
            "html": f"""
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
                    <p style="font-size: 16px;">Per completare la transazione è pregato di contattare il venditore alla seguente email: {seller_email}</p>
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
            """,
        }
    
    @staticmethod
    def _build_seller_message(auction_id, winning_amount, winner_email):
        return {
            "subject": f"📢 Asta conclusa! Oggetto aggiudicato - Asta #{auction_id}",
            "body": f"""
                Ottime notizie!

                La tua asta su BuySellChain si è conclusa con successo. Un acquirente si è aggiudicato l'oggetto!

                DETTAGLI DELLA VENDITA:
                - ID Asta: #{auction_id}
                - Importo Finale: € {winning_amount}
                - Vincitore: {winner_email}

                Ti invitiamo a contattare l'acquirente all'indirizzo email sopra indicato per concordare i dettagli della spedizione e del pagamento, oppure accedi alla tua dashboard per gestire l'ordine.

                Grazie per aver scelto BuySellChain,
                Il team di BuySellChain
                """,
            "html": f"""
            <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="background-color: #3b82f6; padding: 30px 20px; text-align: center; color: white;">
                    <h1 style="margin: 0; font-size: 28px; letter-spacing: 1px;">ASTA CONCLUSA! 🏷️</h1>
                </div>
                <div style="padding: 30px 20px; color: #333333; line-height: 1.6; background-color: #ffffff;">
                    <p style="font-size: 16px;">Gentile Venditore,</p>
                    <p style="font-size: 16px;">Siamo lieti di comunicarti che la tua asta su <strong>BuySellChain</strong> è terminata ed è stata aggiudicata con successo.</p>
                    
                    <div style="background-color: #f8fafc; padding: 20px; border-left: 5px solid #3b82f6; margin: 25px 0; border-radius: 4px;">
                        <h3 style="margin-top: 0; color: #1e293b; font-size: 18px;">Riepilogo della Vendita</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; color: #64748b; font-weight: bold; width: 40%;">Codice Asta:</td>
                                <td style="padding: 8px 0; color: #0f172a;">#{auction_id}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #64748b; font-weight: bold;">Prezzo di Vendita:</td>
                                <td style="padding: 8px 0; color: #3b82f6; font-weight: bold; font-size: 18px;">€ {winning_amount}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #64748b; font-weight: bold;">Vincitore:</td>
                                <td style="padding: 8px 0; color: #0f172a; font-style: italic;">{winner_email}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <p style="font-size: 16px;"><strong>Cosa fare ora?</strong></p>
                    <p style="font-size: 15px; color: #475569;">Puoi contattare direttamente l'acquirente tramite l'email indicata sopra per finalizzare la transazione o gestire la spedizione tramite la tua area riservata.</p>
                    
                    <div style="text-align: center; margin: 35px 0;">
                        <a href="http://127.0.0.1:5000/auction/{auction_id}" style="background-color: #3b82f6; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px; display: inline-block;">Gestisci la Vendita</a>
                    </div>
                </div>
                <div style="background-color: #f1f5f9; padding: 20px; text-align: center; font-size: 13px; color: #64748b; border-top: 1px solid #e2e8f0;">
                    <p style="margin: 0 0 10px 0;">Hai ricevuto questa email perché hai un'asta attiva su BuySellChain.</p>
                    <p style="margin: 0;">&copy; 2026 BuySellChain. Tutti i diritti riservati.</p>
                </div>
            </div>
            """,
        }

    @staticmethod
    def _build_loser_message(auction_id, winning_amount, reason_label):
        return {
            "subject": f"Esito asta #{auction_id} su BuySellChain",
            "body": f"""
                Ciao,

                L'asta #{auction_id} si è conclusa e questa volta la tua offerta non è risultata vincente.

                Motivo della perdita: {reason_label}

                Importo vincente: € {winning_amount}

                Continua a partecipare: troverai presto altre aste interessanti su BuySellChain.

                Grazie per aver partecipato,
                Il team di BuySellChain
                """,
            "html": f"""
            <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="background-color: #ef4444; padding: 30px 20px; text-align: center; color: white;">
                    <h1 style="margin: 0; font-size: 26px; letter-spacing: 0.5px;">Esito dell'asta</h1>
                </div>
                <div style="padding: 30px 20px; color: #333333; line-height: 1.6; background-color: #ffffff;">
                    <p style="font-size: 16px;">Ciao,</p>
                    <p style="font-size: 16px;">L'asta <strong>#{auction_id}</strong> si è conclusa e questa volta la tua offerta non è risultata vincente.</p>
                    <div style="background-color: #fef2f2; padding: 20px; border-left: 5px solid #ef4444; margin: 25px 0; border-radius: 4px;">
                        <h3 style="margin-top: 0; color: #7f1d1d; font-size: 18px;">Motivo della perdita</h3>
                        <p style="margin: 0; color: #991b1b; font-weight: 600;">{reason_label}</p>
                    </div>
                    <p style="font-size: 16px; margin-bottom: 0;">Importo vincente: <strong>€ {winning_amount}</strong></p>
                </div>
                <div style="background-color: #f1f5f9; padding: 20px; text-align: center; font-size: 13px; color: #64748b; border-top: 1px solid #e2e8f0;">
                    <p style="margin: 0 0 10px 0;">Hai ricevuto questa email perché hai partecipato a un'asta su BuySellChain.</p>
                    <p style="margin: 0;">&copy; 2026 BuySellChain. Tutti i diritti riservati.</p>
                </div>
            </div>
            """,
        }

    @staticmethod
    def send_email_to_winner_seller(winner_id, seller_id, auction_id, auction_data):
        mail = current_app.extensions.get('mail')
        recipient_email_winner = EmailService._get_user_email(winner_id)
        recipient_email_seller = EmailService._get_user_email(seller_id)
        current_app.logger.info(f"Preparing to send email to winner: {winner_id} -> {recipient_email_winner}")
        current_app.logger.info(f"Preparing to send email to seller: {seller_id} -> {recipient_email_seller}")
        try:
            if not recipient_email_winner:
                return {"success": False, "error": f"Email not found for user {winner_id}"}
            if not recipient_email_seller:
                return {"success": False, "error": f"Email not found for user {seller_id}"}
            
            winning_amount = EmailService._format_amount(auction_data.get('high_bid_amount', 0))
            
            # Crea e invia email al vincitore, inserendo all'interno del body la mail del venditore
            content_winner = EmailService._build_winner_message(auction_id, winning_amount, recipient_email_seller)
            msg_winner = Message(subject=content_winner["subject"], recipients=[recipient_email_winner])
            msg_winner.body = content_winner["body"]
            msg_winner.html = content_winner["html"]
            mail.send(msg_winner)
            
            # Crea e invia email al venditore, inserendo all'interno del body la mail del vincitore
            content_seller = EmailService._build_seller_message(auction_id, winning_amount, recipient_email_winner)
            msg_seller = Message(subject=content_seller["subject"], recipients=[recipient_email_seller])
            msg_seller.body = content_seller["body"]
            msg_seller.html = content_seller["html"]
            mail.send(msg_seller)
            
            current_app.logger.info(f"Sending email to winner {winner_id} for auction {auction_id} with data: {auction_data}")
            current_app.logger.info(f"Sending email to seller {seller_id} for auction {auction_id} with data: {auction_data}")
            return {"success": True}
        except Exception as e:
            current_app.logger.error(f"Error sending email: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def send_email_to_participants(auction_id, auction_data, bids_list):
        mail = current_app.extensions.get('mail')

        try:
            winning_bids = [
                bid for bid in bids_list
                if str(bid.get("status", "")).lower() == BidStatus.ACCEPTED.value
            ]

            def bid_timestamp(bid):
                parsed_timestamp = EmailService._parse_bid_timestamp(bid.get("timestamp"))
                return parsed_timestamp or datetime.min

            winning_bid = None
            if winning_bids:
                winning_bid = max(
                    winning_bids,
                    key=lambda bid: (float(bid.get("bid_amount", 0)), bid_timestamp(bid)),
                )

            winning_amount = EmailService._format_amount(
                winning_bid.get("bid_amount", auction_data.get("high_bid_amount", 0)) if winning_bid else auction_data.get("high_bid_amount", 0)
            )
            winning_bidder_id = winning_bid.get("bidder_id") if winning_bid else auction_data.get("high_bidder_id")
            winning_bid_amount = float(winning_bid.get("bid_amount", 0)) if winning_bid else float(auction_data.get("high_bid_amount", 0) or 0)
            winning_bid_time = bid_timestamp(winning_bid) if winning_bid else None


            seller_id = auction_data.get("seller_id")
            # Manda l'email al vincitore e al seller.
            EmailService.send_email_to_winner_seller(winning_bidder_id, seller_id, auction_id, auction_data)

            bids_by_user = {}
            for bid in bids_list:
                bidder_id = bid.get("bidder_id")
                if not bidder_id:
                    continue
                bids_by_user.setdefault(bidder_id, []).append(bid)

            for bidder_id, user_bids in bids_by_user.items():
                recipient_email = EmailService._get_user_email(bidder_id)
                if not recipient_email:
                    current_app.logger.warning(f"No email found for participant {bidder_id} in auction {auction_id}")
                    continue

                is_winner = bidder_id == winning_bidder_id
                if not is_winner: # manda le email ai solo partecipanti, all winner la manda prima 
                    accepted_bids = [
                        bid for bid in user_bids
                        if str(bid.get("status", "")).lower() == BidStatus.ACCEPTED.value
                    ]

                    if not winning_bid:
                        reason_label = "Non hai mai avuto offerte valide"
                    elif not accepted_bids:
                        reason_label = "Non hai mai avuto offerte valide"
                    else:
                        best_user_bid = max(
                            accepted_bids,
                            key=lambda bid: (float(bid.get("bid_amount", 0)), bid_timestamp(bid)),
                        )
                        best_user_amount = float(best_user_bid.get("bid_amount", 0) or 0)
                        best_user_timestamp = bid_timestamp(best_user_bid)

                        if best_user_amount < winning_bid_amount:
                            reason_label = "Hai offerto troppo poco"
                        elif best_user_amount == winning_bid_amount and winning_bid_time and best_user_timestamp and best_user_timestamp < winning_bid_time:
                            reason_label = "Hai offerto quanto il vincitore, ma il timestamp tuo era troppo datato"
                        else:
                            reason_label = "Non hai mai avuto offerte valide"

                    content = EmailService._build_loser_message(auction_id, winning_amount, reason_label)

                msg = Message(subject=content["subject"], recipients=[recipient_email])
                msg.body = content["body"]
                msg.html = content["html"]
                mail.send(msg)

            current_app.logger.info(
                f"Sent auction result emails for auction {auction_id} to {len(bids_by_user)} participants"
            )
            return {"success": True, "participants": len(bids_by_user)}
        except Exception as e:
            current_app.logger.error(f"Error sending participant emails: {str(e)}")
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
                recipients=["francosalvucci14@gmail.com","ionut.roma9@gmail.com"] 
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

