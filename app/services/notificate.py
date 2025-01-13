from sqlalchemy.ext.asyncio import AsyncSession
from app.controllers.DefaultControllers import get_events, get_users, create_notification
from app.schemas.DefaultSchemas.notificationSchema import NotificationBase
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import asyncio

async def convert_to_datetime(date_string):
    formats = ["%d %B, %H:%M", "%Y-%m-%dT%H:%M"]
    for date_format in formats:
        try:
            datetime_object = datetime.strptime(date_string, date_format)
            if "%Y" not in date_format:
                datetime_object = datetime_object.replace(year=datetime.now().year)
            return datetime_object
        except ValueError:
            continue

async def send_notification(body: str, to_email: str, db: AsyncSession, event_id: int, user_id: int, task_id: int, subject: str = "Lembrete"):
    # Configurações do servidor SMTP do Gmail
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = "seu_email@gmail.com"  
    smtp_password = "sua_senha_ou_app_password" 

    # Cria a mensagem MIME
    message = MIMEMultipart()
    message["From"] = smtp_username
    message["To"] = to_email
    message["Subject"] = subject

    # Adiciona o corpo do email
    message.attach(MIMEText(body, "plain"))

    # Inicia a conexão com o servidor SMTP
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(smtp_username, to_email, message.as_string())
        await create_notification(db, NotificationBase(message=f"Email enviado com sucesso para {to_email}", send=True, user_id=user_id, event_id=event_id, task_id=task_id, view=False))

    except Exception as e:
        await create_notification(db, NotificationBase(message=f"Erro ao enviar email para {to_email}: {e}", send=True, user_id=user_id, event_id=event_id, task_id=task_id, view=False))

async def check_and_notify(db: AsyncSession):
    now = datetime.now()
    notifications = []
    result = await get_events(db, 0, 0, "", "Events")

    for event in result:
        time_diff: datetime = await convert_to_datetime(event.date) - now
        days_until_event = time_diff.day
        for task in event.tasks:
            try:
                if not task.ready and now < await convert_to_datetime(event.date):
                    users_id = [event.user_id]
                    
                    for event_user_rel in event.event_users:
                        users_id.append(event_user_rel.user_id)
                    
                    users = await get_users(db, 0, 0, f"id+in+{",".join(users_id)}", "User")
                    for user in users:
                        notifications.append(asyncio.create_task(send_notification(f"O Evento {event.name} tem a tarefa pendente: {task.name}, faltam {days_until_event} dias!!!!", user.email, db, event.id, user.id, task.id, "Lembrete de Vencimento!!!!")))
             
                if not task.ready and now > await convert_to_datetime(event.date):
                    users_id = [event.user_id]
                    
                    for event_user_rel in event.event_users:
                        users_id.append(event_user_rel.user_id)
                    
                    users = await get_users(db, 0, 0, f"id+in+{",".join(users_id)}", "User")
                    for user in users:
                        notifications.append(asyncio.create_task(send_notification(f"O Evento {event.name} tem a tarefa pendente: {task.name}, está atrasada!!!!", user.email, db, event.id, user.id, task.id, "Lembrete de Atraso!!!!")))
            
            except Exception as e:
                await create_notification(db, NotificationBase(message=f"Erro ao enviar a notificação: {e}", send=False, user_id=event.user_id, event_id=event.id, task_id=task.id, view=False))

    await asyncio.gather(notifications)
