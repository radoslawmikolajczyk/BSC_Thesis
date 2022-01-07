import cv2


cap = cv2.VideoCapture('http://live.uci.agh.edu.pl/video/stream1.cgi?start=1543408695')
i = 0
counter = 50
while cap.isOpened():
    ret, frame = cap.read()
    if not ret or i == 100:
        break
    counter -= 1
    if counter == 0:
        cv2.imwrite('images/Frame' + str(i) + '.jpg', frame)
        i += 1
        counter = 50

cap.release()
cv2.destroyAllWindows()
