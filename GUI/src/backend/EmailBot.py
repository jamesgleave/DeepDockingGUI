import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailNotificationSettings:
    PHASE_CHANGE_UPDATE = False
    ITERATION_CHANGE_UPDATE = True
    FINAL_PHASE_START_UPDATE = False
    FINAL_PHASE_FINISH_UPDATE = False
    PROJECT_START_UPDATE = False
    PROJECT_FINISH_UPDATE = False

    EMAIL_NOTIFICATIONS = False

    @staticmethod
    def ChangeSettings(phase_change,
                       itr_change,
                       final_phase_start,
                       final_phase_end,
                       project_start,
                       project_finish,
                       email_notifications):

        EmailNotificationSettings.PHASE_CHANGE_UPDATE = phase_change and email_notifications
        EmailNotificationSettings.ITERATION_CHANGE_UPDATE = itr_change and email_notifications
        EmailNotificationSettings.FINAL_PHASE_START_UPDATE = final_phase_start and email_notifications
        EmailNotificationSettings.FINAL_PHASE_FINISH_UPDATE = final_phase_end and email_notifications
        EmailNotificationSettings.PROJECT_START_UPDATE = project_start and email_notifications
        EmailNotificationSettings.PROJECT_FINISH_UPDATE = project_finish and email_notifications
        EmailNotificationSettings.EMAIL_NOTIFICATIONS = email_notifications and email_notifications

    @staticmethod
    def toString():
        return f"PHASE_CHANGE_UPDATE: {EmailNotificationSettings.PHASE_CHANGE_UPDATE}, " \
               f"ITERATION_CHANGE_UPDATE: {EmailNotificationSettings.ITERATION_CHANGE_UPDATE}, " \
               f"FINAL_PHASE_START_UPDATE: {EmailNotificationSettings.FINAL_PHASE_START_UPDATE}, " \
               f"FINAL_PHASE_FINISH_UPDATE: {EmailNotificationSettings.FINAL_PHASE_FINISH_UPDATE}, " \
               f"PROJECT_START_UPDATE: {EmailNotificationSettings.PROJECT_START_UPDATE}, " \
               f"PROJECT_FINISH_UPDATE: {EmailNotificationSettings.PROJECT_FINISH_UPDATE}, " \
               f"EMAIL_NOTIFICATIONS: {EmailNotificationSettings.EMAIL_NOTIFICATIONS}"


class EmailBot:
    def __init__(self, address, password):
        self.s = smtplib.SMTP(host='smtp.gmail.com', port=587)
        self.s.starttls()
        self.s.login(address, password)

        self.address = address
        self.password = password

    def send_message(self, recipient, subject, message):
        msg = MIMEMultipart()  # create a message

        # setup the parameters of the message
        msg['From'] = self.address
        msg['To'] = recipient
        msg['Subject'] = subject

        # add in the message body
        msg.attach(MIMEText(message, 'plain'))

        # send the message via the server set up earlier.
        self.s.send_message(msg)

    def send_iteration_change_update(self, user, to, project_name, new_iteration):
        prev_itr = new_iteration - 1
        message = f"Hello {user},\n\nyour Deep Docking project {project_name} has completed iteration {prev_itr} " \
                  f"and is now on iteration {new_iteration}. For further details, visit 'web-address'. \n" \
                  f"If you would like to stop receiving updates, log into 'web-address' and turn off email notifications." \
                  f"\n\nCheers,\nDeepDockingBot"

        self.send_message(to, "Iteration Complete", message)

    def send_project_started_update(self, user, to, project_name):
        message = f"Hello {user},\n\nyour Deep Docking project {project_name} has begun. " \
                  f"For further details, visit 'web-address'. \n" \
                  f"If you would like to stop receiving updates, " \
                  f"log into 'web-address' and turn off email notifications." \
                  f"\n\nCheers,\nDeepDockingBot"

        self.send_message(to, "Project Started", message)

    def send_queue_position_update(self, user, to, project_name, queue_position):
        pass

    def send_project_finished_update(self, user, to, project_name):
        pass

    @staticmethod
    def get_user_pw():
        return open("/Users/martingleave/Documents/DeepDocking/DeepDockingGUI/GUI/src/backend/email.txt").read().split(" ")

    @staticmethod
    def get_user_email():
        import json

        # load up the data we have from installation
        with open('src/backend/db.json') as user_db:
            db = user_db.read()
            database = json.loads(db)
        return database["email"]
