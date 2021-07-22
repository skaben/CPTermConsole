#!/usr/bin/python3
# -*- coding: utf-8 -*-
import curses
import random
import time
import json
import threading
from math import floor

termConf = dict()
termData = dict()

def millis():
    global termConf, termData
    return (time.time() - termConf['startTime']) * 1000.0

def readDBParameters(checkInterval=2):
    global termConf, termData
    while True:
        if termConf['forceClose']:
            break
        if not termConf['isDBUpdating']:
            termConf['isDBUpdating'] = True
            with open(termConf['confPath'] + termConf['confName'], 'r') as f:
                termData = json.load(f) 
            termConf['isDBUpdating'] = False
        time.sleep(checkInterval)

def initCurses():
    global termConf, termData
    global curses
    curses.initscr()
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(termConf['MAIN_COLOR']['pair'], termConf['MAIN_COLOR']['fg'], termConf['MAIN_COLOR']['bg'])
    curses.init_pair(termConf['HL_COLOR']['pair'], termConf['HL_COLOR']['fg'], termConf['HL_COLOR']['bg'])
    curses.init_pair(termConf['HL_1_COLOR']['pair'], termConf['HL_1_COLOR']['fg'], termConf['HL_1_COLOR']['bg'])
    curses.noecho()
    curses.raw()
    curses.curs_set(0)

def charGen():
    global termConf, termData
    charFlag = 1
    termConf['playChars'] = []
    for i in range(termData['numChars']):
        charFlag = 1
        while charFlag:
            charFlag = 0
            tmpChar = random.randint(0,255)
            for k in range(len(termConf['playChars'])):
                if (termConf['playChars'][k] == tmpChar):
                    charFlag = 1
        termConf['playChars'].append(tmpChar)

def matrixGen():
    global termConf, termData
    termConf['matrix'] = []
    charGen()
    for i in range(termData['rows']):
        tmpList = []
        for j in range(termData['cols']):
            tmpList.append(termConf['playChars'][random.randint(0,termData['numChars']-1)])
        termConf['matrix'].append(tmpList)

def codeGen():
    global termConf, termData
    dirFlag = 0
    i = 0
    col = random.randint(0, termData['cols']-1)
    row = random.randint(0, termData['rows']-1)
    termConf['codeList'].append(termConf['matrix'][col][row])
    for i in range(1,termData['hackLen']):
        if(dirFlag == 0):
            row = (row + random.randint(1, termData['rows']+1)) % 8
            termConf['codeList'].append(termConf['matrix'][col][row])
            dirFlag = 1
        else:
            col = (col + random.randint(1, termData['cols']+1)) % 8
            termConf['codeList'].append(termConf['matrix'][col][row])
            dirFlag = 0
    termConf['codeList'].reverse()
    for i in range(termData['hackLen']):
        termConf['codeString'] += "{:02x} ".format(termConf['codeList'][i])

def matrixPrint():
    global termConf, termData
    termConf['matrixWin'].clear()
    for i in range(termData['rows']):
        for j in range(termData['cols']):
            termConf['matrixWin'].addstr(i, j*3, "{:02x} ".format(termConf['matrix'][i][j]), 
                curses.color_pair(termConf['MAIN_COLOR']['pair']))
    termConf['matrixWin'].refresh()

def outWin(win, y, x, text, color):
    win.clear()
    win.addstr(y, x, text, curses.color_pair(color))
    win.refresh()

def printElMatrix(row,col,color):
    global termConf, termData
    if (termConf['matrix'][row][col] != ''):
        termConf['matrixWin'].addstr(row, col*3, "{:02x} ".format(termConf['matrix'][row][col]),color) 
    else:
        termConf['matrixWin'].addstr(row, col*3, "   ",color) 
                
def hlPos(row, col, direction):
    global termConf, termData
    if (not direction):
        for j in range(termData['cols']):
            printElMatrix(row, j, curses.color_pair(termConf['HL_COLOR']['pair']))
        for i in range(termData['rows']):
            printElMatrix(i, col, curses.color_pair(termConf['HL_1_COLOR']['pair']))
    else:
        for i in range(termData['rows']):
            printElMatrix(i, col, curses.color_pair(termConf['HL_COLOR']['pair']))
        for j in range(termData['cols']):
            printElMatrix(row, j, curses.color_pair(termConf['HL_1_COLOR']['pair']))
    printElMatrix(row, col, curses.color_pair(termConf['MAIN_COLOR']['pair'])|curses.A_REVERSE)
    termConf['matrixWin'].refresh()

def unhlPos(row, col):
    global termConf, termData
    for j in range(termData['cols']):
        printElMatrix(row, j, curses.color_pair(termConf['MAIN_COLOR']['pair']))
    for i in range(termData['rows']):
        printElMatrix(i, col, curses.color_pair(termConf['MAIN_COLOR']['pair']))
    termConf['matrixWin'].refresh()

def compareLists():
    global termConf, termData
    for i in range(termData['hackLen']):
        indBuf = len(termConf['buffList']) - 1 - i
        indCode = len(termConf['codeList']) - 1 - i
        if (termConf['buffList'][indBuf] != termConf['codeList'][indCode]):
            return False
    return True

def playHack():
    global termConf, termData
    dirFlag = 1 # fix rows
    row = 0
    col = 0
    startTime = 0
    curTime = 0
    termConf['matrixWin'].nodelay(True)
    termConf['matrixWin'].keypad(True)
    unhlPos(row, col)
    hlPos(row, col, dirFlag)
    while True:
        if (termConf['timeFlag'] == 1):
            curTime = millis()
            if ((curTime - startTime) >= 100):
                startTime = curTime
                termData['timeOut'] -= 1
                timeToStr()
                outWin(termConf['timerWin'], 0, 0, termConf['timeStr'], termConf['MAIN_COLOR']['pair'])
                if (termData['timeOut'] <= 0):
                    doLose()
        key = termConf['matrixWin'].getch()
        if dirFlag:
            if key == curses.KEY_LEFT or key == 260 or key == ord('A') or key == ord('a'):
                unhlPos(row,col)
                col -= 1
                if col == -1:
                    col = termData['cols'] - 1
                hlPos(row, col, dirFlag)
            if key == curses.KEY_RIGHT or key == 261 or key == ord('D') or key == ord('d'):
                unhlPos(row,col)
                col = (col + 1) % termData['cols']
                hlPos(row, col, dirFlag)
        else:
            if key == curses.KEY_UP or key == 259 or key == ord('W') or key == ord('w'):
                unhlPos(row,col)
                row -= 1
                if row == -1:
                    row = termData['rows'] - 1
                hlPos(row,col, dirFlag)
            if key == curses.KEY_DOWN or key == 258 or key == ord('S') or key == ord('s'):
                unhlPos(row,col)
                row = (row + 1) % termData['rows']
                hlPos(row, col, dirFlag)
        if key == curses.KEY_ENTER or key == 10 or key == 13:
            if (termConf['timeFlag'] == 0):
                startTime = millis()
                termConf['timeFlag'] = 1
            if (termConf['matrix'][row][col] != ''):
                unhlPos(row,col)
                termConf['buffList'].append(termConf['matrix'][row][col])
                termConf['buffString'] += "{:02x} ".format(termConf['matrix'][row][col]) + " "
                outWin(termConf['bufferWin'], 1, 0, "BUFFER: {:s}".format(termConf['buffString']), termConf['MAIN_COLOR']['pair'])
                termConf['matrix'][row][col] = ''
                dirFlag = (dirFlag + 1) % 2
                hlPos(row, col, dirFlag)
                if (len(termConf['buffList'])>=termData['hackLen']):
                    if(compareLists()):
                        doWin()
                    elif (len(termConf['buffList'])>termData['buffLen']):
                        doLose()

def doWin():
    print("YOU WIN!")
    raise SystemExit

def doLose():
    print("YOU LOSE!")
    raise SystemExit

def timeToStr():
    global termConf, termData
    decs = int(termData['timeOut'] - 10*floor(termData['timeOut']/10))
    secs = int(termData['timeOut']/10%60)
    mins = int(termData['timeOut']/10/60%60)
    hours = int(termData['timeOut']/10/60/60%60)
    termConf['timeStr'] = "{:02d}:{:02d}:{:02d}.{:02d}".format(hours, mins, secs, decs)

def startTerm(stdscr):
    global termConf, termData

    initCurses()

    termConf['headWin'] = curses.newwin(4, 60, 0, 0)
    termConf['timerWin'] = curses.newwin(4, 20, 0, 60)
    termConf['bufferWin'] = curses.newwin(3, 80, 4, 0)
    termConf['matrixWin'] = curses.newwin(16, 24, 7, 0)
    termConf['codeWin'] = curses.newwin(16, 48, 7, 25)

    outWin(termConf['headWin'], 0, 0, termData['headText'], termConf['MAIN_COLOR']['pair'])
    outWin(termConf['bufferWin'], 1, 0, "BUFFER: {:s}".format(termConf['buffString']), termConf['MAIN_COLOR']['pair'])

    matrixGen()
    codeGen()

    outWin(termConf['codeWin'], 0, 0, "SELECT CODE: {:s}".format(termConf['codeString']), termConf['MAIN_COLOR']['pair'])
    matrixPrint()

    timeToStr()
    outWin(termConf['timerWin'], 0, 0, termConf['timeStr'], termConf['MAIN_COLOR']['pair'])

    playHack()

def main(stdscr):
    global termConf, termData
    with open("conf/CPTermConst.json", 'r') as f:
            termConf = json.load(f) 
    termConf['startTime'] = millis()
    dbThread = threading.Thread(target=readDBParameters, args=(2,))
    dbThread.start()
    time.sleep(1)
    while termConf['isDBUpdating']:
        # Ожидаем, пока обновится состояние из БД
        pass
    startTerm(stdscr)

curses.wrapper(main)