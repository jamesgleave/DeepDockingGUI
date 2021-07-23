"""
The event handler for the backend.
This class handles all callbacks from withing the backend loop.
"""

from .EmailBot import *


class EventHandler:
    @staticmethod
    def OnBackendStart(backend):
        print("Event Handled Backend Start")

    @staticmethod
    def OnProjectRunPhase(backend):
        print("Event Handled Run Phase")
        if EmailNotificationSettings.PROJECT_START_UPDATE:
            address, pw = EmailBot.get_user_pw()
            bot = EmailBot(address=address, password=pw)
            user_email = EmailBot.get_user_email()

            # Return if we have no email entered
            if user_email == "NA":
                return

    @staticmethod
    def OnPhaseChange(backend):
        print("Event Handled Phase Change")
        if EmailNotificationSettings.PHASE_CHANGE_UPDATE:
            address, pw = EmailBot.get_user_pw()
            bot = EmailBot(address=address, password=pw)
            user_email = EmailBot.get_user_email()

            # Return if we have no email entered
            if user_email == "NA":
                return

    @staticmethod
    def OnIterationChange(backend):
        print("Event Handled Iteration Change")
        try:
            if EmailNotificationSettings.ITERATION_CHANGE_UPDATE:
                address, pw = EmailBot.get_user_pw()
                bot = EmailBot(address=address, password=pw)
                user_email = EmailBot.get_user_email()

                # Return if we have no email entered
                if user_email == "NA" and backend.loaded_project_information['specifications']['iteration'] > 1:
                    return

                bot.send_iteration_change_update(backend.user_data["username"],
                                                user_email,
                                                backend.loaded_project_name,
                                                backend.loaded_project_information['specifications']['iteration'])
        except FileNotFoundError:
            print("Email notifications not implemented yet...")

    @staticmethod
    def OnFinalPhaseStart(backend):
        print("Event Handled Final Phase Start")
        if EmailNotificationSettings.FINAL_PHASE_START_UPDATE:
            pass

    @staticmethod
    def OnFinalPhaseEnd(backend):
        print("Event Handled Final Phase End")
        if EmailNotificationSettings.FINAL_PHASE_FINISH_UPDATE:
            pass

    @staticmethod
    def OnProjectFinished(backend):
        print("Event Handled Project Finished")
        if EmailNotificationSettings.PROJECT_FINISH_UPDATE:
            pass

    @staticmethod
    def OnDataReadError(backend):
        print("Event Handled Data Read Error")

    @staticmethod
    def OnErrorDetected(backend):
        print("Event Handled Error Detected")



