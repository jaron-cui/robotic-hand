from gui import RecognizerFigure
from recognizer import HandRecognizer
from threading import Thread

def main():
    recognizer = HandRecognizer()
    fig = RecognizerFigure(recognizer)
    fig.show()
    recognizer.run()
    fig.close()

if __name__ == "__main__":
    main()