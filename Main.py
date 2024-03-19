import sys
import cv2
import csv
import dlib
import os.path
import warnings
import datetime
import threading
import pandas as pd
from deepface import DeepFace
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtGui import QImage, QFont
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView

from GUI import Ui_MainWindow
from ThreadsHandler import progessThread

warnings.filterwarnings('ignore')


def add_record_to_csv(filename, record):
    # Open the CSV file in append mode
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)

        # Write the record to the CSV file
        writer.writerow(record)


class Main:
    def __init__(self):

        # Path of the user
        self.stress_message = None
        self.face_analysis = None
        self.users_csv_path = "users.csv"
        self.patient_report_csv_path = "patient_report.csv"

        # Admin code premises
        self.admin_code = "123456789"

        # Loading the stress Model
        self.stress_labels = {
            'angry': 'Chronic Stress',
            'fear': 'Chronic Stress',
            'surprise': 'No Stress',
            'disgust': 'Acute Stress',
            'sad': 'Acute Stress',
            'neutral': 'Low Stress',
            'happy': 'No Stress'
        }

        # Current user
        self.current_user = ""
        self.current_user_id = ""
        self.current_user_role = ""

        # Camera Flags
        self.camera_id = 0
        self.detector = None
        self.face_frame = None
        self.camera_flag = False
        self.camera_frame = None
        self.camera_btn_text = "Start Camera"

        # Questioning_variables
        self.current_question = 0
        self.depression_score = 0
        self.answers = []
        self.questions = [
            "Little interest or pleasure in doing things?",
            "Feeling down, depressed, or hopeless?",
            "Trouble falling or staying asleep, or sleeping too much?",
            "Feeling tired or having little energy?",
            "Poor appetite or overeating?",
            "Feeling bad about yourself - or that you are a failure or have let yourself or your family down?",
            "Trouble concentrating on things, such as reading the newspaper or watching television?",
            "Moving or speaking so slowly that other people could have noticed?",
            "Thoughts that you would be better off dead, or of hurting yourself in some way?",
            "Have you had trouble enjoying activities that you used to find pleasurable?",
            "Have you felt Worthless or Guilty?",
            "Have you had thoughts of death or suicide?",
            "Trouble controlling your anger?",
            "Have you had trouble feeling hopeful or optimistic about the future?",
            "Do you feel that your depression symptoms have significantly affected your daily functioning?",
            "Have you had difficulty controlling or stopping repetitive thoughts or behaviors?",
            "Physical symptoms such as headache or muscle pain without any apparent cause?"
        ]
        self.medication_dict = {
            "Low Stress": ["\nCitalopram (Celexa)", "\nEscitalopram (Lexapro)",
                           "\nFluoxetine (Prozac, Prozac weekly)",
                           "\nParoxetine (Paxil, Paxil CR)"],
            "Chronic Stress": ["\nSertraline (Zoloft)", "\nVenlafaxine (Effexor, Effexor XR)",
                               "\nDesvenlafaxine (Pristiq)", "\nDuloxetine (Cymbalta)"],
            "Acute Stress": ["\nBupropion (Wellbutrin, Wellbutrin SR, Wellbutrin XL)",
                             "\nMirtazapine (Remeron)", "Vortioxetine (Trintellix)",
                             "\nVilazodone (Viibryd)", "Trazodone", "Buspirone (Buspar)",
                             "\nHydroxyzine (Atarax, Vistaril)"]
        }

        # Connect Backend with the front end
        self.MainWindow = QtWidgets.QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.MainWindow)

        # Set the maximum value to 100 for each progress bar
        self.ui.progressBar.setMaximum(100)
        self.ui.progressBar_2.setMaximum(100)
        self.ui.progressBar_3.setMaximum(100)
        self.ui.progressBar_4.setMaximum(100)

        # Buttons Connections
        self.initial_settings()
        self.button_connection()
        self.navigation_buttons()

        # Background Thread to update the frames
        self.t = progessThread(parent=None)
        self.t.any_signal.connect(self.update_thread_values)
        self.t.start()

    # When start the window show these settings
    def suggest_medication(self):

        stress_level = self.stress_labels[self.face_analysis['dominant_emotion']]


        if stress_level in self.medication_dict:
            suggested_meds = self.medication_dict[stress_level]
            self.ui.label_30.setText(f"Suggested medications for {stress_level}:\n{', '.join(suggested_meds)}")
        else:
            self.ui.label_30.setText("Invalid stress level.")

        # Display the Empty Stress Message
        if self.stress_message == "No Stress":
            self.ui.label_30.setText("No Medicine required you are fine...")

        # Display the medicine frame
        self.ui.frame_10.setVisible(True)

    def initial_settings(self):
        self.ui.frame_7.setVisible(True)
        self.ui.label_11.setVisible(False)
        self.ui.label_12.setVisible(False)
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.stackedWidget_2.setCurrentIndex(0)

        # Check for the users data exists
        if not os.path.exists(self.users_csv_path):
            user_df = pd.DataFrame(columns=["ID", "EMAIL", "NAME", 'PASSWORD', "ROLE"])
            user_df.to_csv(self.users_csv_path, index=False)

        # Check for the patient report exists
        if not os.path.exists(self.patient_report_csv_path):
            patient_df = pd.DataFrame(columns=["ID", "PATIENT NAME", "DATE", "TIME", "DEPRESSION LEVEL"])
            patient_df.to_csv(self.patient_report_csv_path, index=False)

    def stop_thread(self):
        self.camera_flag = False

    def open_patient_report(self):

        # Load the users list
        data_frame = pd.read_csv(self.patient_report_csv_path)

        # Extract the patients data only
        data_frame = data_frame[
            (data_frame['PATIENT NAME'] == self.current_user) & (data_frame['ID'] == self.current_user_id)]

        # Clear the table
        self.ui.tableWidget_2.clear()

        # Set the number of rows and columns in the table
        self.ui.tableWidget_2.setRowCount(data_frame.shape[0])
        self.ui.tableWidget_2.setColumnCount(data_frame.shape[1])

        # Set the headers of the table
        self.ui.tableWidget_2.setHorizontalHeaderLabels(data_frame.columns)

        # Iterate over the data and add it to the table widget
        for row in range(data_frame.shape[0]):
            for col in range(data_frame.shape[1]):
                item = QTableWidgetItem(str(data_frame.iloc[row, col]))
                self.ui.tableWidget_2.setItem(row, col, item)

        header = self.ui.tableWidget_2.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        font = QFont()
        font.setPointSize(16)  # Set the desired font size
        header.setFont(font)

        self.ui.stackedWidget.setCurrentIndex(6)

    def open_patient_list(self):

        # Load the users list
        data_frame = pd.read_csv(self.users_csv_path)

        # Extract the patients data only
        data_frame = data_frame[data_frame['ROLE'] == 'user']

        # Clear the table
        self.ui.tableWidget.clear()

        # Set the number of rows and columns in the table
        self.ui.tableWidget.setRowCount(data_frame.shape[0])
        self.ui.tableWidget.setColumnCount(data_frame.shape[1])

        # Set the headers of the table
        self.ui.tableWidget.setHorizontalHeaderLabels(data_frame.columns)

        # Iterate over the data and add it to the table widget
        for row in range(data_frame.shape[0]):
            for col in range(data_frame.shape[1]):
                item = QTableWidgetItem(str(data_frame.iloc[row, col]))
                self.ui.tableWidget.setItem(row, col, item)

        header = self.ui.tableWidget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        font = QFont()
        font.setPointSize(16)  # Set the desired font size
        header.setFont(font)

        self.ui.stackedWidget.setCurrentIndex(1)

    def open_question_window(self):
        self.camera_flag = False
        self.current_question = 0
        self.depression_score = 0
        self.answers = []
        self.ui.stackedWidget.setCurrentIndex(3)

    def go_back_home(self):
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.stackedWidget_2.setCurrentIndex(2)

    def next_question(self):
        if self.current_question + 1 < len(self.questions):
            self.current_question += 1
            self.ui.label_27.setText(self.questions[self.current_question])

            # Get the answer
            option = ""
            if self.ui.radioButton_3.isChecked():
                option = "Not at all"
                self.depression_score += 1
            elif self.ui.radioButton_4.isChecked():
                option = "Several days"
                self.depression_score += 2
            elif self.ui.radioButton_6.isChecked():
                option = "Nearly Every day"
                self.depression_score += 3
            elif self.ui.radioButton_5.isChecked():
                option = "More than Half the days"
                self.depression_score += 4

            self.answers.append(option)

        else:

            self.stress_message = "No Stress"

            if self.face_analysis['dominant_emotion'] not in self.stress_labels.keys():
                self.stress_message = "No Stress"
            elif self.depression_score < 20 and \
                    self.stress_labels[self.face_analysis['dominant_emotion']] == "Low Stress":
                self.stress_message = "No Depression"
            elif 20 <= self.depression_score < 30 and \
                    self.stress_labels[self.face_analysis['dominant_emotion']] == "Low Stress":
                self.stress_message = "Normal Depression"
            elif 30 <= self.depression_score <= 40 and \
                    self.stress_labels[self.face_analysis['dominant_emotion']] == "Low Stress":
                self.stress_message = "High Depression"
            elif self.depression_score < 40 and \
                    self.stress_labels[self.face_analysis['dominant_emotion']] == "Chronic Stress":
                self.stress_message = "Normal Depression"
            elif 40 <= self.depression_score < 60 and \
                    self.stress_labels[self.face_analysis['dominant_emotion']] == "Chronic Stress":
                self.stress_message = "High Depression"
            elif 60 <= self.depression_score <= 70 and \
                    self.stress_labels[self.face_analysis['dominant_emotion']] == "Chronic Stress":
                self.stress_message = "High Depression"
            elif self.depression_score < 50 and \
                    self.stress_labels[self.face_analysis['dominant_emotion']] == "Acute Stress":
                self.stress_message = "Normal Depression"
            elif 50 <= self.depression_score <= 70 and \
                    self.stress_labels[self.face_analysis['dominant_emotion']] == "Acute Stress":
                self.stress_message = "High Depression"

            self.ui.label_28.setText("You have: " + self.stress_message)
            self.ui.frame_10.setVisible(False)
            self.ui.label_30.setText("Suggested Medicines:")
            self.ui.stackedWidget.setCurrentIndex(4)

    def record_stress(self):
        if self.stress_message is not None:

            now = datetime.datetime.now()
            date = now.strftime('%Y-%m-%d')
            time = now.strftime('%H:%M:%S')
            username = self.current_user
            id = self.current_user_id

            if self.stress_message:
                stress = self.stress_message
            else:
                stress = self.stress_message

            # Save the record
            add_record_to_csv(self.patient_report_csv_path, [id, username, date, time, stress])

            self.go_back_home()

    def open_camera(self):
        self.ui.pushButton_9.setVisible(False)
        self.ui.stackedWidget.setCurrentIndex(2)

    def start_camera(self):

        # Check with the button text the thread is working or not
        if self.ui.pushButton_8.text() == "Start Camera":

            # Change the tn text of button
            self.camera_btn_text = "Stop Stream"

            # Check if the picture is taken or not
            self.camera_flag = True

            # Start the face detector
            self.detector = dlib.get_frontal_face_detector()

            # Start the selected
            cap = cv2.VideoCapture(self.camera_id)

            # Start the loop
            while True:

                # Read the frame
                ret_val, frame = cap.read()

                # Check if the frame is capture
                if not ret_val:
                    self.face_frame = None
                    self.camera_frame = None
                    self.camera_flag = False
                    self.camera_btn_text = "Start Camera"
                    break

                # Reset Everything
                if not self.camera_flag:
                    self.face_frame = None
                    self.camera_frame = None
                    self.camera_flag = False
                    self.camera_btn_text = "Start Camera"
                    break

                try:
                    # convert the frame into grayscale
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                except:
                    continue

                # Get the face coordinates
                faces = self.detector(gray)

                # Check face or not found
                if len(faces) != 0:

                    # Now get all the face in the frame
                    for face in faces:
                        x1 = face.left() - 20
                        y1 = face.top() - 20
                        x2 = face.right() + 20
                        y2 = face.bottom() + 20

                        # Now get the reign of interest of the face and get the prediction over that face
                        self.face_frame = frame[y1:y2, x1:x2].copy()

                        # Save the face image
                        cv2.imwrite("face.jpg", frame[y1:y2, x1:x2])

                        # Draw the rectangle
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2, cv2.LINE_AA)

                        # Save the face analysis
                        try:
                            self.face_analysis = DeepFace.analyze(img_path="face.jpg",
                                                                  actions=('emotion', 'gender'),
                                                                  enforce_detection=False)
                            self.ui.pushButton_9.setVisible(True)
                        except:
                            self.ui.pushButton_9.setVisible(False)
                            continue

                        # Stress Level
                        if self.face_analysis['dominant_emotion'] in self.stress_labels.keys():
                            cv2.putText(frame, "Stress:" + self.stress_labels[self.face_analysis['dominant_emotion']],
                                        (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                            cv2.putText(frame,
                                        f"Gender: {self.face_analysis['gender']}",
                                        (x1, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                # Copy the current frame
                self.camera_frame = frame.copy()

            # Release the camera
            cap.release()

        else:
            self.face_frame = None
            self.camera_frame = None
            self.camera_flag = False
            self.camera_btn_text = "Start Camera"

    def update_thread_values(self):

        self.ui.pushButton_8.setText(self.camera_btn_text)

        # Display the frame of the live stream
        if self.camera_frame is None:
            self.ui.label_16.clear()
        else:
            result = cv2.cvtColor(self.camera_frame, cv2.COLOR_BGR2RGB)
            height, width, channel = result.shape
            step = channel * width
            qImg = QImage(result.data, width, height, step, QImage.Format_RGB888)
            self.ui.label_16.setPixmap(QtGui.QPixmap(qImg))

            # Check for the face information is their
            if self.face_analysis is not None:
                # Display Stress Scores
                self.ui.progressBar.setValue(self.face_analysis['emotion']['sad'])
                self.ui.progressBar_2.setValue(self.face_analysis['emotion']['angry'])
                self.ui.progressBar_3.setValue(self.face_analysis['emotion']['neutral'])
                self.ui.progressBar_4.setValue(self.face_analysis['emotion']['happy'])

    def login(self):

        # Get the login user email and password
        user_email = self.ui.lineEdit.text()
        password = self.ui.lineEdit_2.text()

        if user_email != "" and password != "" and "@" in user_email:
            try:
                login_users = pd.read_csv(self.users_csv_path)
                user = login_users[(login_users['EMAIL'].astype(str) == str(user_email)) &
                                   (login_users['PASSWORD'].astype(str) == password)].values[0]
                self.current_user = user[1]
                self.current_user_id = user[0]
                self.current_user_role = user[-1]
                if self.current_user_role == "user":
                    self.ui.pushButton_4.setVisible(False)
                else:
                    self.ui.pushButton_4.setVisible(True)
                self.ui.stackedWidget_2.setCurrentIndex(2)
            except:
                self.ui.label_11.setVisible(True)
                self.ui.label_11.setText("Note! Incorrect email or password")
        else:
            self.ui.label_11.setVisible(True)
            self.ui.label_11.setText("Note! Some fields are empty")

    def logout(self):
        self.current_user = ""
        self.current_user_id = ""
        self.current_user_role = ""
        self.ui.lineEdit.clear()
        self.ui.lineEdit_2.clear()
        self.ui.stackedWidget_2.setCurrentIndex(0)

    # Function to register new user
    def register(self):
        self.ui.lineEdit_3.clear()
        self.ui.lineEdit_4.clear()
        self.ui.lineEdit_5.clear()
        self.ui.stackedWidget_2.setCurrentIndex(1)

    def add_new_user(self):

        # retrieve the information from the register window
        email = self.ui.lineEdit_3.text()
        name = self.ui.lineEdit_7.text()
        password = self.ui.lineEdit_4.text()
        re_password = self.ui.lineEdit_5.text()
        role = ""

        if self.ui.radioButton.isChecked():
            role = "admin"
        elif self.ui.radioButton_2.isChecked():
            role = "user"

        # Checking if the required fields are not empty
        if email == "" or password == "" or re_password == "" or role == "" or name == "":
            self.ui.label_12.setVisible(True)
            self.ui.label_12.setText("Note! Some fields are empty!")
            return

        # Checking if the email is valid
        if "@" not in email:
            self.ui.label_12.setVisible(True)
            self.ui.label_12.setText("Note! Email not Valid!")
            return

        # Check the password matches or not
        if password != re_password:
            self.ui.label_12.setVisible(True)
            self.ui.label_12.setText("Note! Password didn't matched!")
            return

        # Load the users record
        login_users = pd.read_csv(self.users_csv_path)

        # Check for the user already exits
        if email in login_users.EMAIL.values:
            self.ui.label_12.setVisible(True)
            self.ui.label_12.setText("Note! Email Already exists")
            return

        # Check if the Registrar is admin or not
        if self.ui.radioButton.isChecked():
            if self.admin_code != self.ui.lineEdit_6.text():
                self.ui.label_12.setVisible(True)
                self.ui.label_12.setText("Note! Admin code not Matched")
                return

        # New User ID
        new_user_id = sorted(login_users.ID.values)[-1] + 1

        # Adding new record
        new_rec = pd.DataFrame([[new_user_id, email, name, password, role]],
                               columns=['ID', 'EMAIL', 'NAME', 'PASSWORD', 'ROLE'])

        # Combining the new record with the older record
        users = pd.concat([login_users, new_rec])

        # Saving the record
        users.to_csv(self.users_csv_path, index=False)

        # After registering it will go to the login screen
        self.ui.stackedWidget_2.setCurrentIndex(0)

    def button_connection(self):

        # Button Connections to their functions
        self.ui.pushButton.clicked.connect(self.login)
        self.ui.pushButton_2.clicked.connect(self.register)
        self.ui.pushButton_3.clicked.connect(self.add_new_user)
        self.ui.pushButton_4.clicked.connect(self.open_patient_list)
        self.ui.pushButton_6.clicked.connect(self.open_patient_report)
        self.ui.pushButton_7.clicked.connect(self.logout)
        self.ui.pushButton_9.clicked.connect(self.open_question_window)
        self.ui.pushButton_16.clicked.connect(self.next_question)
        self.ui.pushButton_17.clicked.connect(self.record_stress)
        self.ui.pushButton_18.clicked.connect(self.go_back_home)

        # Text Change
        self.ui.lineEdit.returnPressed.connect(self.login)
        self.ui.lineEdit_2.returnPressed.connect(self.login)

        # Single line functions of the radiobutton and Line Edits
        self.ui.radioButton.clicked.connect(lambda: self.ui.frame_7.setVisible(True))
        self.ui.radioButton_2.clicked.connect(lambda: self.ui.frame_7.setVisible(False))
        self.ui.lineEdit.textChanged.connect(lambda: self.ui.label_11.setVisible(False))
        self.ui.lineEdit.textChanged.connect(lambda: self.ui.label_11.setVisible(False))
        self.ui.pushButton_8.clicked.connect(lambda: threading.Thread(target=self.start_camera).start())

    def navigation_buttons(self):
        self.ui.pushButton_5.clicked.connect(self.open_camera)
        self.ui.pushButton_21.clicked.connect(self.suggest_medication)
        self.ui.pushButton_10.clicked.connect(lambda: self.ui.stackedWidget_2.setCurrentIndex(0))
        self.ui.pushButton_11.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(0))
        self.ui.pushButton_12.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(0))
        self.ui.pushButton_13.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(0))
        self.ui.pushButton_14.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(2))
        self.ui.pushButton_15.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(3))


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    application = Main()
    application.MainWindow.show()
    app.exec_()
    application.stop_thread()
    sys.exit(0)
