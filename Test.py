from deepface import DeepFace
import cv2

cam = cv2.VideoCapture(0)

while cam.isOpened():

    ret, frame = cam.read()

    if ret:

        frame = cv2.flip(frame, 1)

        cv2.imwrite("frame.jpg", frame)

        try:
            faces = DeepFace.extract_faces("frame.jpg")
        except:
            cv2.imshow("frame", frame)
            continue

        for face in faces:
            x = face['facial_area']['x'] - 50
            y = face['facial_area']['y'] - 50
            w = face['facial_area']['w'] + 50
            h = face['facial_area']['h'] + 50

            # print(face_analysis)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2, cv2.LINE_AA)

            # cv2.imshow("face", face['face'])

            # Save the face image
            cv2.imwrite("face.jpg", frame[y:y + h, x:x + w])

            try:
                face_analysis = DeepFace.analyze(img_path="face.jpg")
                print(face_analysis)
            except:
                pass

        # # Emotion Model
        # cv2.putText(frame, "Emotion:" + face_analysis['dominant_emotion'],
        #             (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        #
        # # Gender Model
        # cv2.putText(frame, "Gender:" + face_analysis['gender'], (x, y - 30),
        #             cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        cv2.imshow("frame", frame)
        key = cv2.waitKey(1)

        if key == ord('q'):
            break

cam.release()
cv2.destroyAllWindows()

# import torch
# print(torch.cuda.is_available())

# import tensorflow as tf
#
# print(tf.config.list_physical_devices('GPU'))
# for device in tf.config.list_physical_devices('GPU'):
#     print(device)
