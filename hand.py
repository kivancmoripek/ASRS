import cv2
import mediapipe as mp
import time
import snap7
from snap7.util import *

time.sleep(2.0)

mp_draw = mp.solutions.drawing_utils
mp_hand = mp.solutions.hands

tipIds = [4, 8, 12, 16, 20]

video = cv2.VideoCapture(0)

plc = snap7.client.Client()
plc.connect('192.168.56.105', 0, 1)

sAl = plc.db_read(7, 0, 1)
set_bool(sAl, 0, 2, False)
plc.db_write(7, 0, sAl)
sBirak = plc.db_read(7, 0, 1)
set_bool(sBirak, 0, 3, False)
plc.db_write(7, 0, sBirak)
data = plc.db_read(7, 1, 1)
set_usint(data, 0, 0)
plc.db_write(7, 1, data)
data = plc.db_read(7, 2, 1)
set_usint(data, 0, 0)
plc.db_write(7, 2, data)

STATE_OPERATION = 1
STATE_SHELF = 2
STATE_SLOT = 3

state = STATE_OPERATION
operation = None
shelf = 0
slot = 0

left_input_delay = 90
right_input_delay = 100
left_gesture_counter = 0
right_gesture_counter = 0
current_gesture_left = None
current_gesture_right = None
left_fingers = 0
right_fingers = 0

def count_fingers(lmList, hand_label):
    fingers = []
    # Thumb
    if hand_label == "Right":
        if lmList[tipIds[0]][1] < lmList[tipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)
    else:
        if lmList[tipIds[0]][1] > lmList[tipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)
    
    # Other fingers
    for id in range(1, 5):
        if lmList[tipIds[id]][2] < lmList[tipIds[id] - 2][2]:
            fingers.append(1)
        else:
            fingers.append(0)
    
    return fingers

def detect_fist(lmList):
    bent_fingers = [tipIds[i] for i in range(1, 5) if lmList[tipIds[i]][2] > lmList[tipIds[i] - 2][2]]
    return len(bent_fingers) == 4

def detect_spidey(lmList):
    thumb_up = lmList[tipIds[0]][1] < lmList[tipIds[0] - 1][1]
    thumb_up_l = lmList[tipIds[0]][1] > lmList[tipIds[0] - 1][1]
    index_up = lmList[tipIds[1]][2] < lmList[tipIds[1] - 2][2]
    pinky_up = lmList[tipIds[4]][2] < lmList[tipIds[4] - 2][2]
    bent_fingers = [tipIds[i] for i in [2, 3] if lmList[tipIds[i]][2] > lmList[tipIds[i] - 2][2]]
    return (thumb_up or thumb_up_l) and index_up and pinky_up and len(bent_fingers) == 2

with mp_hand.Hands(min_detection_confidence=0.9, min_tracking_confidence=0.9) as hands:
    while True:
        ret, image = video.read()
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = hands.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        h, w, _ = image.shape
        middle_x = w // 2
        
        cv2.line(image, (middle_x, 0), (middle_x, h), (255, 0, 0), 2)
        
        if results.multi_hand_landmarks:
            for hand_landmarks, hand_classification in zip(results.multi_hand_landmarks, results.multi_handedness):
                lmList = []
                for id, lm in enumerate(hand_landmarks.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lmList.append([id, cx, cy])
                
                hand_label = hand_classification.classification[0].label
                fingers = count_fingers(lmList, hand_label)
                total = fingers.count(1)
                
                if lmList[9][1] < middle_x:
                    left_fingers = total
                    
                    detected_gesture = None
                    if state == STATE_OPERATION:
                        if detect_fist(lmList):
                            detected_gesture = "Al"
                        elif detect_spidey(lmList):
                            detected_gesture = "Birak"

                    if detected_gesture == current_gesture_left:
                        left_gesture_counter += 1
                    else:
                        left_gesture_counter = 0
                        current_gesture_left = detected_gesture

                    if left_gesture_counter >= left_input_delay:
                        if state == STATE_OPERATION:
                            operation = detected_gesture
                            if operation == "Al":
                                sAl = plc.db_read(7, 0, 1)
                                set_bool(sAl, 0, 2, True)
                                plc.db_write(7, 0, sAl)
                                sBirak = plc.db_read(7, 0, 1)
                                set_bool(sBirak, 0, 3, False)
                                plc.db_write(7, 0, sBirak)
                            elif operation == "Birak":
                                set_bool(sAl, 0, 2, False)
                                plc.db_write(7, 0, sAl)
                                sBirak = plc.db_read(7, 0, 1)
                                set_bool(sBirak, 0, 3, True)
                                plc.db_write(7, 0, sBirak)
                            cv2.putText(image, f"{operation}! Raf No Girin.", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                            cv2.imshow("AS/RS Kamera", image)
                            cv2.waitKey(2000)
                            state = STATE_SHELF
                        elif state == STATE_SHELF:
                            shelf = left_fingers + right_fingers
                            sRaf = plc.db_read(7, 1, 1)
                            set_usint(sRaf, 0, shelf)
                            plc.db_write(7, 1, sRaf)
                            cv2.putText(image, f"Raf No:{shelf} Sira No Girin.", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                            cv2.imshow("AS/RS Kamera", image)
                            cv2.waitKey(2000)
                            state = STATE_SLOT
                            left_fingers = 0
                            right_fingers = 0                            
                        elif state == STATE_SLOT:
                            slot = left_fingers + right_fingers
                            sUrun = plc.db_read(7, 2, 1)
                            set_usint(sUrun, 0, slot)
                            plc.db_write(7, 2, sUrun)
                            cv2.putText(image, f"{operation}, Raf No:{shelf}, Sira No:{slot}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                            cv2.imshow("AS/RS Kamera", image)
                            cv2.waitKey(2000)
                            state = STATE_OPERATION
                            left_fingers = 0
                            right_fingers = 0                            
                        left_gesture_counter = 0
                
                else:
                    right_fingers = total
                    
                    detected_gesture = None
                    if state == STATE_OPERATION:
                        if detect_fist(lmList):
                            detected_gesture = "Al"
                        elif detect_spidey(lmList):
                            detected_gesture = "Birak"

                    if detected_gesture == current_gesture_right:
                        right_gesture_counter += 1
                    else:
                        right_gesture_counter = 0
                        current_gesture_right = detected_gesture

                    if right_gesture_counter >= right_input_delay:
                        if state == STATE_OPERATION:
                            operation = detected_gesture
                            if operation == "Al":
                                sAl = plc.db_read(7, 0, 1)
                                set_bool(sAl, 0, 2, True)
                                plc.db_write(7, 0, sAl)
                                sBirak = plc.db_read(7, 0, 1)
                                set_bool(sBirak, 0, 3, False)
                                plc.db_write(7, 0, sBirak)
                            elif operation == "Birak":
                                set_bool(sAl, 0, 2, False)
                                plc.db_write(7, 0, sAl)
                                sBirak = plc.db_read(7, 0, 1)
                                set_bool(sBirak, 0, 3, True)
                                plc.db_write(7, 0, sBirak)
                            cv2.putText(image, f"{operation}! Raf No Girin.", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                            cv2.imshow("AS/RS Kamera", image)
                            cv2.waitKey(2000)
                            state = STATE_SHELF
                        elif state == STATE_SHELF:
                            shelf = left_fingers + right_fingers
                            sRaf = plc.db_read(7, 1, 1)
                            set_usint(sRaf, 0, shelf)
                            plc.db_write(7, 1, sRaf)
                            cv2.putText(image, f"Raf No:{shelf} Sira No Girin.", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                            cv2.imshow("AS/RS Kamera", image)
                            cv2.waitKey(2000)
                            state = STATE_SLOT
                            left_fingers = 0
                            right_fingers = 0
                        elif state == STATE_SLOT:
                            slot = left_fingers + right_fingers
                            sUrun = plc.db_read(7, 2, 1)
                            set_usint(sUrun, 0, slot)
                            plc.db_write(7, 2, sUrun)
                            cv2.putText(image, f"{operation}, Raf No:{shelf}, Sira No:{slot}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                            cv2.imshow("AS/RS Kamera", image)
                            cv2.waitKey(2000)
                            state = STATE_OPERATION
                            left_fingers = 0
                            right_fingers = 0    
                        right_gesture_counter = 0
                mp_draw.draw_landmarks(image, hand_landmarks, mp_hand.HAND_CONNECTIONS)
        
        cv2.imshow("AS/RS Kamera", image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

video.release()
cv2.destroyAllWindows()
