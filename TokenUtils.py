import CUDAPolskaPreparing

testData = ["1.txt","2.txt","3.txt"]

alphabet = "qwertyuiopasdfghjklzxcvbnm"
alphabet += alphabet.upper()
alphabet += "_"

numbers = "0123456789"
special = "+-().*/^,"
seps = " \t\n"

class Token:
    def __init__(self, data):
        self.data = data
        self.type = -1
    def __str__(self):
        return "Token{Type: " + Token.TokenType.getType(self.type) + ", Data: \"" + self.data + "\"}"
    def __repr__(self):
        return self.__str__()
    class TokenType:
        NUMBER = 1
        DOT = 2
        SC_OPEN = 3
        SC_CLOSE = 4
        FUNC_OPEN = 5
        ID = 6
        PLUS = 7
        MINUS = 8
        MULT = 9
        DIV = 10
        POWER = 11
        FNUMBER = 12
        UMINUS = 13 # унарные
        UPLUS = 14
        SEP = 15 # разделитель-запятая
        UNKNOWN = -1
        def getType(_id):
            try:
                i = int(_id)
                for F in dir(Token.TokenType):
                    if F[0] == '_':
                        continue
                    if getattr(Token.TokenType, F) == i:
                        return F
            except Exception as err:
                print(err)
                return "UNKNOWN"
    priority = {
        TokenType.UMINUS: 4,
        TokenType.UPLUS: 4,
        TokenType.POWER: 3,
        TokenType.MULT: 2,
        TokenType.DIV: 2,
        TokenType.PLUS: 1,
        TokenType.MINUS: 1,
    }
    rightOps = [
        TokenType.UMINUS,
        TokenType.UPLUS,
        TokenType.POWER
    ]

    def getTokenPriority(tokenType):
        return Token.priority.get(tokenType, -1)
class StringReader:
    def __init__(self, string):
        self.string = string
        self.pos = 0
    def getSymb(self):
        try:
            return self.string[self.pos]
        except:
            return None
    def forward(self):
        symb = self.getSymb()
        self.pos += 1
        return symb
    def backward(self):
        symb = self.getSymb()
        self.pos -= 1
        return symb
    def setPos(self, pos):
        symb = self.getSymb()
        self.pos = pos
        return symb
    def getPos(self):
        return self.pos
    def isEnd(self):
        return (self.pos >= len(self.string))
    def isValid(self):
        return (self.pos >= 0) and not self.isEnd()
    def peek(self):
        try:
            return self.string[self.pos + 1]
        except:
            return None
    def bPeek(self):
        if self.pos == 0:
            return self.getSymb()
        try:
            return self.string[self.pos - 1]
        except:
            return None

class States:
    S = 1
    N = 2
    SP = 3 # специальный символ( +-(). )
    W = 4
    Err = 5
    F = -1
    Unknown = -2
    def nextState(curr, symb):
        if curr == States.S: #### S
            if symb in numbers:
                return States.N
            if symb in alphabet:
                return States.W
            if symb in special:
                return States.SP
            if symb in seps:
                return States.S
        if curr == States.N: #### N
            if symb in numbers:
                return States.N
            if symb in alphabet:
                return States.Err
            if symb in special:
                return States.F
            if symb in seps:
                return States.F
        if curr == States.SP: #### SP
            return States.F
        if curr == States.W: #### W
            if symb in numbers:
                return States.W
            if symb in alphabet:
                return States.W
            if symb in special:
                return States.F
            if symb in seps:
                return States.F
        if curr == States.Err: #### Err
            return States.Err
        if curr == States.F: #### F
            return States.F
        return States.Unknown
            
        

def rawTokenizator(data):
    rawTokens = []
    s = StringReader(data)

    accum = ""
    currentState = States.S
    while s.bPeek() != None:
        symb = s.forward()
        if symb == None:
            symb = ' '
        currentState = States.nextState(currentState, symb)
        
        if currentState == States.Err:
            raise Exception("Error with make token")
        if currentState == States.Unknown:
            raise Exception("Unknown symbol \"" + symb + "\"")
        if currentState == States.F:
            rawTokens.append(accum)
            accum = ""
            
            currentState = States.S
            s.backward()
        if currentState != States.S:
            accum += symb
    return rawTokens

def rawTokensFinalizer(data):
    tokens = []

    for rawToken in data:
        t = Token(rawToken)
        if rawToken == '.':
            t.type = Token.TokenType.DOT
        elif rawToken == '(':
            t.type = Token.TokenType.SC_OPEN
        elif rawToken == ')':
            t.type = Token.TokenType.SC_CLOSE
        elif rawToken == '+':
            t.type = Token.TokenType.PLUS
        elif rawToken == '-':
            t.type = Token.TokenType.MINUS
        elif rawToken == '*':
            t.type = Token.TokenType.MULT
        elif rawToken == '/':
            t.type = Token.TokenType.DIV
        elif rawToken == '^':
            t.type = Token.TokenType.POWER
        elif rawToken == ',':
            t.type = Token.TokenType.SEP
        else:
            try:
                int(rawToken)
                t.type = Token.TokenType.NUMBER
            except:
                t.type = Token.TokenType.ID
        tokens.append(t)

    return tokens

def tokensFinalizer_2(tokens):
    fTokens = [i for i in tokens]
    for i in range(len(fTokens)):
        try:
            if (fTokens[i+0].type == Token.TokenType.ID and
                fTokens[i+1].type == Token.TokenType.SC_OPEN):
                t = Token(fTokens[i+0].data)
                t.type = Token.TokenType.FUNC_OPEN
                fTokens.pop(i)
                fTokens.pop(i)
                fTokens.insert(i, t)
            elif (fTokens[i+0].type == Token.TokenType.NUMBER and
                fTokens[i+1].type == Token.TokenType.DOT and
                fTokens[i+2].type == Token.TokenType.NUMBER):
                t = Token(fTokens[i+0].data + fTokens[i+1].data + fTokens[i+2].data)
                t.type = Token.TokenType.FNUMBER
                fTokens.pop(i)
                fTokens.pop(i)
                fTokens.pop(i)
                fTokens.insert(i, t)
        except:
            pass
    return fTokens

def unaryOperatorHandler(tokens):
    fTokens = [i for i in tokens]
    expectedID = True
    for i in range(len(fTokens)):
        tokenType = fTokens[i+0].type
        if (tokenType == Token.TokenType.PLUS and expectedID):
            fTokens[i+0].type = Token.TokenType.UPLUS
        elif (tokenType == Token.TokenType.MINUS and expectedID):
            fTokens[i+0].type = Token.TokenType.UMINUS
        elif (tokenType == Token.TokenType.FUNC_OPEN or
            tokenType == Token.TokenType.SC_OPEN or
            tokenType == Token.TokenType.FUNC_OPEN or
            tokenType == Token.TokenType.PLUS or
            tokenType == Token.TokenType.MINUS or
            tokenType == Token.TokenType.MULT or
            tokenType == Token.TokenType.DIV or
            tokenType == Token.TokenType.POWER):
            expectedID = True
        elif (tokenType == Token.TokenType.ID or
        tokenType == Token.TokenType.NUMBER or
        tokenType == Token.TokenType.FNUMBER):
            expectedID = False
    return fTokens

def backwardPolskaNote(tokens):
    stack = []
    out = []

    for t in tokens:
        #print(t, "=======" ,out, "=======", stack)
        # Операнды
        if t.type in (Token.TokenType.ID, Token.TokenType.NUMBER, Token.TokenType.FNUMBER):
            out.append(t)
        # Открывающая скобка или функция
        elif t.type == Token.TokenType.FUNC_OPEN or t.type == Token.TokenType.SC_OPEN:
            stack.append(t)
        # Закрывающая скобка
        elif t.type == Token.TokenType.SC_CLOSE:
            while True:
                if len(stack) == 0:
                    raise Exception("Mismatched parentheses")
                t2 = stack.pop()
                if t2.type == Token.TokenType.FUNC_OPEN:
                    out.append(t2)
                    break
                elif t2.type == Token.TokenType.SC_OPEN:
                    break
                else:
                    out.append(t2)
        # Запятая
        elif t.type == Token.TokenType.SEP:
            while (len(stack) > 0 and
                   stack[-1].type != Token.TokenType.SC_OPEN and
                   stack[-1].type != Token.TokenType.FUNC_OPEN):
                out.append(stack.pop())
        # Точка или неизвестный токен
        elif t.type in (Token.TokenType.DOT, Token.TokenType.UNKNOWN):
            raise Exception("Invalid token")
        # Операторы
        elif t.type in Token.priority:
            while len(stack) and Token.getTokenPriority(stack[-1].type) != -1:
                top_type = stack[-1].type
                if (t.type not in Token.rightOps and
                    Token.getTokenPriority(t.type) <= Token.getTokenPriority(top_type)) or \
                   (t.type in Token.rightOps and
                    Token.getTokenPriority(t.type) < Token.getTokenPriority(top_type)):
                    out.append(stack.pop())
                else:
                    break
            stack.append(t)
    while stack:
        top = stack.pop()
        if top.type in (Token.TokenType.SC_OPEN, Token.TokenType.FUNC_OPEN):
            raise Exception("Mismatched parentheses")
        out.append(top)

    return out


if __name__ == "__main__":
    raw = rawTokenizator("(x*2) + ((-g / sin(6*y)) * z)")
    print(raw)
    print('===')
    tokens = rawTokensFinalizer(raw)
    print(tokens)
    print('===')
    fTokens = tokensFinalizer_2(tokens)
    print(fTokens)
    print('===')
    fTokens2 = unaryOperatorHandler(fTokens)
    print(fTokens2)
    print('===')
    fTokens3 = backwardPolskaNote(fTokens2)
    print(fTokens3)
    print('===')
    print("Errors:",CUDAPolskaPreparing.checkVariables(fTokens3))