from datetime import datetime as dt
from twilio.rest import Client
import datetime
import urllib3
import base64
import json
import face_recognition
import cv2
import numpy as np

video_capture = cv2.VideoCapture(0)

obama_image = face_recognition.load_image_file("obama.jpg")
obama_face_encoding = face_recognition.face_encodings(obama_image)[0]

biden_image = face_recognition.load_image_file("biden.jpg")
biden_face_encoding = face_recognition.face_encodings(biden_image)[0]

twilio_account_sid = "ACac72e3ce4ccf1623a81a0d37c106febd"
twilio_auth_token = "3e15c951600c252d093ed55076867047"
imgur_client_id = "f7e628dbe0ce8c4"

known_face_encodings = [
    obama_face_encoding,
    biden_face_encoding
]
known_face_names = [
    "Barack Obama",
    "Joe Biden"
]

face_locations = []
face_encodings = []
face_names = []
process_this_frame = True
detectedDate = dt.now()

while True:
    ret, frame = video_capture.read()
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = small_frame[:, :, ::-1]
    name = None

    if process_this_frame:
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)

            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
            else:
                name = "Unknown"

            face_names.append(name)

    process_this_frame = not process_this_frame

    for (top, right, bottom, left), name in zip(face_locations, face_names):
        top *= 3
        right *= 4
        bottom *= 5
        left *= 4

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    cv2.imshow('Video', frame)

    b = dt.now()
    isSet = True

    if name is not None:
        if name == "Unknown" and isSet:
            b = detectedDate + datetime.timedelta(0, 5)
            isSet = False

        if dt.now() > b:
            if name == "Unknown":
                current_time = dt.now().strftime("%m-%d-%Y - %H:%M:%S")
                picture_name = 'Intrusion_' + current_time.replace(" ", "_") + '.png'
                cv2.imwrite(picture_name, frame)

                f = open(picture_name, "rb")
                image_data = f.read()

                b64_image = base64.standard_b64encode(image_data)

                headers = {'Authorization': "Client-ID " + imgur_client_id}
                body = {'image': b64_image, 'title': 'Intrusión ' + current_time}

                http = urllib3.PoolManager()
                req = http.request("POST", "https://api.imgur.com/3/upload.json", fields=body, headers=headers)
                response = json.loads(req.data)
                link_uploaded_image = response['data']['link']
                client = Client(twilio_account_sid, twilio_auth_token)
                message = client.messages.create(
                    from_='whatsapp:+14155238886',
                    body="Posible intrusión detectada! Fecha:" + current_time,
                    to="whatsapp:+50237402464",
                    media_url=link_uploaded_image
                )

            isSet = True
            detectedDate = dt.now()

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()
