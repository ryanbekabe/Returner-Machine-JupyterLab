#https://codereview.stackexchange.com/questions/184532/steinhaus-johnson-trotter-algorithm
from sys import exit

def makeList():
    # Just makes a list in an ascending order
    # The ascending order is important!
    # The initial direction is 0 (LEFT)
    LIST = []
    try:
        n = int(input("How many elements?\n> "))
        for i in range(1,n+1):
            LIST.append([i,0])
        getAllPermutations(LIST)
    except ValueError as e:
        print("Value Error : ", e)
        sys.exit(0)

def changeDirections(LIST, MI):
    # self explanatory
    for element in LIST:
        if element[0] > LIST[MI][0]:
            if element[1] == 0:
                element[1] = 1

            elif element[1] == 1:
                element[1] = 0

def swap(LIST, MI):
    # Just swaps the MI with adjacent item based on the MI's direction
    if LIST[MI][1] == 0:
        tempElement = LIST[MI-1]
        LIST[MI-1] = LIST[MI]
        LIST[MI] = tempElement
    elif LIST[MI][1] == 1:
        tempElement = LIST[MI+1]
        LIST[MI+1] = LIST[MI]
        LIST[MI] = tempElement


def findLargestMI(LIST):
    # 0 < -- LEFT
    # 1 > -- RIGHT
    MI = None
    foundMI = False
    for i in LIST:
        # True if the direction of i is left
        if i[1] == 0:
            # If it isn't the first element in the list keep going
            # That's because if the list looks like this <3 <1 <2
            # <3 can't be a Mobile Integer thus it doesn't need
            # to be checked
            if LIST.index(i) != 0:
                    # If it's the first iteration than currentMI is None
                    # that's why i wrote an if-statement
                    if MI == None:
                        # If the current iteration element is bigger than
                        # the neighbor right of it than declare it as
                        # the current Mobile Integer
                        if i[0] > LIST[LIST.index(i) - 1][0]:
                            MI = LIST.index(i)
                            foundMI = True

                    elif MI != None:
                        # Is the current iteration element bigger than
                        # its neighbor
                        # and is it bigger than the current Mobile
                        # Integer?
                        if ( i[0] > LIST[LIST.index(i) - 1][0] ) and ( i[0] > LIST[MI][0] ):
                            MI = LIST.index(i)
                            foundMI = True

    # True if the direction of i is right
        if i[1] == 1:
            # Every following step is the reverse of the code above
            if LIST.index(i) != LIST.index(LIST[-1]):
                    if MI == None:
                        if i[0] > LIST[LIST.index(i) + 1][0]:
                            MI = LIST.index(i)
                            foundMI = True

                    elif MI != None:
                        if ( i[0] > LIST[LIST.index(i) + 1][0]) and ( i[0] > LIST[MI][0]):
                            MI = LIST.index(i)
                            foundMI = True

    if not foundMI:
        # If it's false then there isn't anymore Mobile Integer
        return foundMI

    return MI

def getAllPermutations(LIST):
    # The reason why i change the directions before the swapping
    # is that when i swap the items before the change of directions
    # an other element gets in the place of the Mobile Integer and
    # wrong elements are changed in direction. Further it
    # doesn't affect the procedure
    #LIST.sort(key=lambda x: x[0])
    index = 1
    while True:
        printListWithDirections(LIST, index)
        index += 1
        MI = findLargestMI(LIST)
        if isinstance(MI, bool) and MI == False:
            print("#####END#####")
            break;
        changeDirections(LIST, MI)
        swap(LIST, MI)



def printListWithDirections(LIST, index):
    output = ""
    secondPrint = False
    for i in LIST:
        # Nothing important. I just want the list to be shown
        # in a pretty way for some reason
        if secondPrint:
            output += (" ")
        else:
            secondPrint = True

        if i[1] == 0:
            output += ("<" + str(i[0]))
        elif i[1] == 1:
            output += (str(i[0]) + ">")

    print(str(index)+ ". " + output)


if __name__ == '__main__':
    makeList()