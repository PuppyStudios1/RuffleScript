"""
RuffleScript v1.6 interpreter
============================

(c) 2024 Aaha3

`[!] notice: this interpreter is just a small project and sometimes unstable to use.`

interprets lines of code given in the notebook, or given in a .rfs file.
(check build status if Your rufflescript version is stable)
`[?] TIP: use a .rh (rufflescript header file) to make a package`
( for info on commands, type `help();` )

     ----------------------                             
    ------------------------                            
    ------------------------                            
    ------------------------                            
    -----------%@*@#=%@@%---                            
    -----------%@#--#@*=----                            
    -----------%@+---=*@@---                            
    -----------%@+--#@@@#---                            
     ---------------------       
    
"""
__status__ = "experimental/unstable"
__version__ = "v1.6"


import os,sys
import operator,re
import pandas as pd
import asyncio
import json
import io as _io
import ast
import platform

global io
global inp
global g_variables
global letvar
global functions

variables = {}
functions = {}
vartypes = {}
g_variables = {}
namespaces = {}
types = {"bool":"bool","number":"number","string":"string","any":"any","null":"null"}

inp = ""
runtime_value = " RuntimeValue:"
Runtime_error = " RuntimeError:"
runtime_log = " RuntimeLog:"
br = "}"
bbr = "{"

io = 0
nb = 0
line = 0
rl = False
rt = False

current_namespace = None


try:
    with open("rsconfig.json") as f:
        data = json.load(f)

    rl = data["RuntimeLineSuggestion"] == "on"
    md = data["moduleRuntimeValue"] == "on"
    verb = data["verbose"] == "true"

except FileNotFoundError:
    print("{ ConfigError: rsconfig.json file not found }")
except json.JSONDecodeError:
    print("{ ConfigError: Invalid JSON data in rsconfig.json }")
except KeyError:
    pass
else:
    # Further processing 
    if rl:
        pass
    else:
        pass
    
    if md:
        pass
    else:
        pass
    if verb:
        pass
    else:
        pass

ops = {
    '+': (operator.add, 1),
    '-': (operator.sub, 1),
    '*': (operator.mul, 2),
    '/': (operator.truediv, 2)
}


def get_variable_value(var_name):
    if var_name in variables:
        return variables[var_name]
    else:
        return None
    
def ismath(text):
  """
  Checks if a string represents a valid arithmetic expression.

  Args:
      text: The string to be evaluated.

  Returns:
      True if the string is a valid arithmetic expression, False otherwise.
  """
  operators = "+-*/"
  numbers = "0123456789."  # Allow decimals

  # Check if empty or just whitespace
  if not text.strip():
    return False

  # Initialize variables
  is_operator = False
  has_number = False

  for char in text:
    if char in operators:
      # Consecutive operators or operator at the beginning/end is invalid
      if is_operator or not has_number:
        return False
      is_operator = True
      has_number = False
    elif char in numbers:
      has_number = True
      is_operator = False
    else:
      # Any other character is invalid
      return False
    
def export(name, value):
    env = os.environ.copy()
    env[name] = str(value)  # Ensure value is a string for environment variable
    os.environ.update(env)
    if verb == True:
        print("{ RuntimeValue: exported "+str(name)+" -> '"+str(value)+"' }")
    else:
        pass
    
async def define_function(name, body):
  async def function():
    main(body)
  return function

async def asyn(inp):
    function_name = None
    function_body = []

    # Check if user is defining a function
    if inp.startswith("async func"):
      # Extract function name
      function_name = inp.split()[2]
      function_body = []  # Reset function body
      print(f"{runtime_value} defining async function: {function_name} {br}")
    elif function_name:
      # Add lines to function body
      function_body.append(inp)
      # Check for function definition end (using indentation)
      if inp.endswith("{"):
        inp.replace("}","")
        async_function = await define_function(function_name, "\n".join(function_body))
        function_name = None
        function_body = []
        print(f"{runtime_value} async function '{function_name}' defined. {br}")
    else:
      # Execute simulation if a function is defined
      if async_function:
        try:
          # Call the simulated async function
          result = await async_function()
          print(f"{runtime_value}  created async function '{function_name}' returned: {result} {br}")
        except Exception as e:
          print(f"{Runtime_error}: {e} {br}")

logo = """                    
     ----------------------                            
    ------------------------                            
    ------------------------                            
    ------------------------                            
    -----------%@*@#=%@@%---                            
    -----------%@#--#@*=----                            
    -----------%@+---=*@@---                            
    -----------%@+--#@@@#---                            
     ----------------------       
    
    """


class Node:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right

def parse_expression(expression_string):
    ops = {'+': operator.add, '-': operator.sub, '*': operator.mul, '/': operator.truediv}
    # Corrected regular expression to handle floating-point numbers, integers, and operators
    tokens = re.findall(r'\b\d+\.\d+|\b\d+|\+|\-|\*|\/|\(|\)', expression_string)
    stack = []
    operator_stack = []

    for token in tokens:
        if re.match(r'\b\d+\.\d+|\b\d+', token):
            # Convert token to float if it contains a decimal point
            stack.append(Node(float(token)))
        elif token in ops:
            while operator_stack and operator_stack[-1] != '(' and ops[operator_stack[-1]][1] >= ops[token][1]:
                process_operator(stack, operator_stack.pop())
            operator_stack.append(token)
        elif token == "(":
            operator_stack.append(token)
        elif token == ")":
            while operator_stack and operator_stack[-1] != "(":
                process_operator(stack, operator_stack.pop())
            operator_stack.pop()  # Remove the '('
        else:
            raise ValueError(f"Invalid character: {token}")

    while operator_stack:
        process_operator(stack, operator_stack.pop())

    if len(stack) != 1:
        raise ValueError("Invalid expression: Missing closing parenthesis or extra operands")

    return stack[0]

def process_operator(stack, op):
    right = stack.pop()
    left = stack.pop()
    stack.append(Node(ops[op][0], left, right))

def evaluate_expression(node):
    if isinstance(node.value, (int, float)):
        return node.value
    elif callable(node.value):
        return node.value(evaluate_expression(node.left), evaluate_expression(node.right))
    else:
        raise TypeError(f"{bbr}{Runtime_error} invalid node value: {node.value} {br}")

def intr():
    interface_pattern = r"^interface\s+(.+?)\s*\{(.*?)\}\}$"
    match = re.search(interface_pattern, data, re.DOTALL)
    if match:
        return {"name": match.group(1), "body": match.group(2)}
    else:
        print("{ RuntimeError: invalid format. Please use 'interface <name> {<lets>}' format. }")

    interface_name = match.group(1)
    lets_block = match.group(2)

    # Process the lets block and store variables
    my_interface = Interface(interface_name)
    for let_inp in lets_block.split(";"):  # Split by semicolons
        let_inp = let_inp.strip()  # Remove leading/trailing whitespaces

        # Split the let inp into parts
        parts = let_inp.split()

        if len(parts) < 2 or parts[0] != "let":
            if parts[0] == "" or parts[0] == " ":
                pass
        else:
            print("{ RuntimeError: Invalid inp in lets block: '"+str(let_inp)+"'. Skipping. }")
            

        try:
            # Extract variable name and value
            var_name = parts[1].strip(":")  # Remove colon if present
            value = int(parts[2]) if parts[2].isdigit() else " ".join(parts[2:])

            my_interface.let(var_name, value)
        except ValueError:
            print("{ RuntimeError: Invalid value in 'let' inp: '"+str(let_inp)+"'. Skipping. }")

    # Print the final state of the interface
    if verb == True:
        print("{ RuntimeValue: ",end="")
        print(my_interface,end="")
        print(" }")
    else:
        pass


def Type(inp=""):
    inp.lower().replace("type")


class Interface:
  def __init__(self, name):
    self.name = name
    

  def let(self, name, value):
    variables[name] = value

  def get(self, name):
    return variables.get(name)

  def __str__(self):
    if not variables:
      return f"{bbr}{runtime_log} interface {self.name} has no variables set. {br}"
    return f"{bbr}{runtime_log} interface {self.name}:\n" + "\n".join(f"{key}: {value}" for key, value in variables.items()+f"{br}")



class TextWrapper:
    def __init__(self, filepath,buffer_size=1024):
        self.filepath = filepath
        self.buffer = ""
        self.buffer_size = buffer_size  # Adjust buffer size as needed

    def read(self):
        if self.buffer:
            data = self.buffer
            self.buffer = ""
            return data

        with open(self.filepath, 'r') as f:
            data = f.read(self.buffer_size)
            self.buffer = data[len(data.splitlines()):]  # Save remaining partial line for next read
            return data.splitlines()

    def readline(self):
        lines = self.read()
        if lines:
            return lines[0] + "\n"
        else:
            return ""
        
    def readlnbin(self):
        with open(self.filepath, 'r+b') as f:
            return f

    def close(self):
        pass  # No explicit closing needed for this custom wrapper
    
    def write(self, data):
        with open(self.filepath, 'a') as f:  # Open in append mode for writing
            f.write(data)
            
    def writebin(self, data):
        with open(self.filepath, 'w+b') as f:  # Open in append mode for writing
            f.write(data)

class namespaces:
    def __init__(self):
        self.buffer = ""
        self.namespace_name = None

    def write(self, data):
        self.buffer += str(data)  # No need for extra newline here

    def getvalue(self):
        return self.buffer

    def readline(self):
        if not self.buffer:
            return ""
        index = self.buffer.find("\n")
        if index == -1:
            line = self.buffer
            self.buffer = ""
            return line
        line = self.buffer[:index]
        self.buffer = self.buffer[index + 1 :]
        return line

    def handle_input(self, command):
        inp = command.lower().strip()
        inp = inp.rstrip("\n")

        if inp == "getvalue()":
            return self.getvalue()
        elif inp.startswith("write(") and inp.endswith(")"):
            text_to_write = inp[6:].strip()  # Remove extra spaces, no need to strip quotes
            text_to_write = text_to_write.replace(")","")
            text_to_write = text_to_write.replace('"',"")
            text_to_write = text_to_write.replace("'","")
            
            self.write(text_to_write)
            if verb == True:
                return "{ RuntimeValue: wrote '"+str(text_to_write)+"' to the buffer in namespace '"+self.namespace_name+"' }"
            else:
                pass
        else:
            return "{ RuntimeError: invalid input. Use 'getvalue()' or 'write (<text>)'. }"
    
class IOBase:
    def __init__(self):
        self.buffer = ""

    # Prompt the user for input and handle inps
    def handle_input(self):
        if "_io.IOBase.write" in inp:
            inp = inp.replace(")","")
            inp = inp.replace("(","")
            inp = inp.replace(";","")
            inp = inp.replace("write","")
            text = inp.replace('"',"")
            text = inp.replace("'","")
            self.write(text)
            if verb == True:
                print("{ RuntimeValue: wrote text '"+text+"' to buffer }")
            else:
                pass
        elif inp == "_io.IOBase.read();":
            print(self.read())
        elif inp == "_io.IOBase.clearBuffer();":
            self.clear()
        else:
            print("{ RuntimeError: invalid _io.IOBase input. }")

    def write(self, data):
        self.buffer += str(data)

    def read(self):
        print(self.buffer)

    def clear(self):
        self.buffer = ""


class BytesIO:

    def __init__(self, file):
        self.file = file

    def __getitem__(self,key):
        if type(key) is int:
            self.file.seek(key)
            return self.file.read(1)
        if type(key) is slice:
            self.file.seek(key.start)
            return self.file.read(key.stop - key.start)

    def __setitem__(self, key, val):
        assert(type(val) == bytes or type(val) == bytearray)
        if type(key) is slice:
            assert(key.stop - key.start == len(val))
            self.file.seek(key.start)
            self.file.write(val)
        if type(key) is int:
            assert(len(val) == 1)
            self.file.seek(key)
            self.file.write(val)

    def close(self):
        self.file.close()


def handle_input(inp):
    global current_namespace

    match = re.match(r'namespace\((.*?)\) \| (.*)', inp)  # Updated regex for namespace()
    if match:
        namespace_name, command = match.groups()
        if namespace_name not in namespaces:
            namespaces[namespace_name] = namespaces()
        current_namespace = namespaces[namespace_name]

        # Set namespace_name only once within the block (if new namespace)
        current_namespace.namespace_name = namespace_name

        if command:
            return current_namespace.handle_input(command)

    if current_namespace is None:
        return "{ RuntimeError: no current namespace selected. Use 'namespace(<name>)' first. }"

    if not command:
        return "{ RuntimeError: invalid input. Enter a command in the current namespace. }"
    return current_namespace.handle_input(command)


def compare_expression(expression):
  try:
    tree = ast.parse(expression)
    operators = ["==", "!=", "<", ">", "<=", ">="]
    for op in operators:
      if op in expression:
        parts = expression.split(op, 1)
        if len(parts) == 2:
          left ,right = parts
          # Evaluate both sides using eval (carefully!)
          left_value = eval(left.strip())
          right_value = eval(right.strip())
          # Compare the evaluated values based on the operator
          if op == "==":
            return left_value == right_value
          elif op == "!=":
            return left_value != right_value
          elif op == "<":
            return left_value < right_value
          elif op == ">":
            return left_value > right_value
          elif op == "<=":
            return left_value <= right_value
          elif op == ">=":
            return left_value >= right_value
        else:
          return False  # Invalid expression (missing operand after operator)

    # No comparison operator found
    return False

  except (SyntaxError, NameError):
    # Handle invalid expressions or variables not defined
    print(f"Invalid expression: {expression}")
    return False


def const_creator():
    
    constants = {}  # Dictionary to store constants

    parts = inp.split("|")

    name, values_str = parts
    name = name.strip()
    values_str = values_str.strip()

    try:
        values = [value.strip() for value in values_str.split(",")]
    except ValueError:
        print("{ RuntimeError: invalid value format. Please separate values with commas. }")
        

    const_declaration = f"const {name} = {{{','.join(values)}}};"
    if verb == True:
        print("{ RuntimeValue: generated const:", const_declaration," }")
    else:
        pass

    # Store constant in the dictionary
    constants[name] = values

    # Print all defined constants
    print("\nAll defined constants:")
    for const_name, const_values in constants.items():
        if len(const_values) == 1:
            print(f"  - {const_name}: {const_values[0]}")
        else:
            print(f"  - {const_name} ({', '.join(const_values)})")


# instances
my_file = IOBase()









# main here ->
def main(inp):
    try:
        global io
        global variables
        
        if nb == 1:
            inp = input("∙> ")
            inp.replace("\n","")
            if ";" not in inp:
                print("{ RuntimeError: exected ';' at the end of line. }")
                exit()
            else:
                pass
            
        else:
            pass
        if not inp:
            if verb == True:
                print("{ RuntimeValue: -> None }")
                return None
            else:
                pass

        

        # Print the string and handle return statement
        elif inp.startswith("return"):
            inp = inp.replace("return", "")
            inp = inp.replace(";", "")
            inp = inp.replace('"',"")
            inp = inp.replace('(',"")
            inp = inp.replace(')',"")
            inp = inp.replace("'","")
            if verb == True:
                print("{ RuntimeValue: ",str(inp)," }")
                return f"print({inp})"
            else:
                print(str(inp))
            
            
            if '"' or "'" in inp:
                if verb == True:
                    print("{ RuntimeValue: " + str(inp) + " }")
                else:
                    print(str(inp))
            else:
                    
                if '"' or "'" not in inp:
                    if inp in variables:
                        if verb == True:
                            print("{ RuntimeValue: " + variables[inp] + " }")
                        else:
                            pass
                elif '"' or "'" in inp and inp in variables:
                    if rl == True:
                        print("{ RuntimeLine: a variable name was in quotes, did you mean the variable? }")
                    else:
                        pass
                elif "'" or '"' not in inp and inp not in variables:
                    print("{ RuntimeError: '"+str(inp)+"' is not defined")
                    
                elif ismath(inp) == True:
                    inp = inp.replace("return","")
                    inp = inp.replace(" ","")
                    
                    if '"' or "'" in inp:
                        if verb == True:
                            print("{ RuntimeValue: " + str(inp) + " }")
                        else:
                            print(str(inp))
                    else:
                        try:
                            expression_tree = parse_expression(inp)
                            result = evaluate_expression(expression_tree)
                            if verb == True:
                                print("{ RuntimeValue: "+str(inp)+" -> "+str(result)+" }")
                            else:
                                pass
                        except (ValueError, TypeError) as e:
                            print("{ RuntimeError: "+str(e)+" }")
                
            
            inp = inp.replace(";", "")
            inp = inp.replace('"', "")
        
        elif inp.startswith("typeface"):
            inp = inp.replace("typeface", "")
            inp = inp.replace(";", "")
            inp = inp.replace('"',"")
            inp = inp.replace('(',"")
            inp = inp.replace(')',"")
            inp = inp.replace("'","")
            print(str(inp))
            return f"print({inp})"
            
            
            
            if '"' or "'" in inp:
                    print(str(inp))
            else:
                    
                if '"' or "'" not in inp:
                    if inp in variables:
                        print(variables[inp])
                elif '"' or "'" in inp and inp in variables:
                    if rl == True:
                        print("{ RuntimeLine: a variable name was in quotes, did you mean the variable? }")
                    else:
                        pass
                elif "'" or '"' not in inp and inp not in variables:
                    print("{ RuntimeError: '"+str(inp)+"' is not defined")
                    
                elif ismath(inp) == True:
                    inp = inp.replace("typeface","")
                    inp = inp.replace(" ","")
                    
                    if '"' or "'" in inp:
                        print(str(inp))
                    else:
                        try:
                            expression_tree = parse_expression(inp)
                            result = evaluate_expression(expression_tree)
                            print(str(result))
                        except (ValueError, TypeError) as e:
                            print("{ RuntimeError: "+str(e)+" }")
                
            
            inp = inp.replace(";", "")
            inp = inp.replace('"', "")
        
        elif inp.startswith("func"):
            """
            func main() {
                // code here
            }
            """
            parts = inp.strip().split()  # Split into meaningful parts
            name = parts[1]
            args_list = parts[2].split(",")  # Extract arguments
            body = inp.split("{")[1].split("}")[0].strip()
            functions[name] = [body.split(";")]
            print("\n",dict)

        if ismath(inp) == True:        
            try:
                expression_tree = parse_expression(inp)
                result = evaluate_expression(expression_tree)
                if verb == True:
                    print("{ RuntimeValue: "+str(inp)+" -> "+str(result)+" }")
                else:
                    pass
            except (ValueError, TypeError) as e:
                print("{ RuntimeError: "+str(e)+" }")
        
        
        elif "->" not in inp and inp.startswith("prompt"):
            try:
                inp = inp.replace("prompt","")
                inp = inp.replace("(","")
                inp = inp.replace(")","")
                inp = inp.replace("'","")
                inp = inp.replace('"',"")
                inp = inp.replace(";","")
                input(inp)
                return "input(inp)"
            except:
                print("{ RuntimeError: expected expression. }")
                
        elif "->" in inp and inp.startswith("promptSync"):
            try:
                inp = inp.replace("promptSync","")
                inp = inp.replace("(","")
                inp = inp.replace(")","")
                inp = inp.replace(";","")
                inp = inp.replace("'","")
                inp = inp.replace('"',"")
                inp = inp.replace("->","")
                prompttokens = inp.split()
                prompt = input(inp)
                variables[prompttokens[2]] = prompt
                prvar = prompttokens[2]
                return str(prvar)+" = input(inp)"
            except:
                print("{ RuntimeError: expected expression. }")
        
        elif inp.startswith("var "):
            parts = inp.split("->")
            if len(parts) != 2:
                print("{ RuntimeError: invalid variable declaration syntax. Use 'var <variable_name> -> <value>;' }")
            else:
                variable_name = parts[0].strip().replace("var ", "")
                variable_value = parts[1].strip().replace('"', "")
                variable_value = parts[1].strip().replace(';', "")
                if variable_name and variable_value in vartypes:
                    if vartypes[variable_name] != "boolean":
                        print("{ RuntimeError: variable types don't mach (boolean) }")
                    else:
                        pass
                    if vartypes[variable_name] != "number":
                        print("{ RuntimeError: variable types don't mach (number) }")
                    else:
                        pass
                    if vartypes[variable_name] != "string":
                        print("{ RuntimeError: variable types don't mach (string) }")
                    else:
                        pass
                
                g_variables[variable_name]=variable_value
                
                if isinstance(inp,int):
                    vartypes[variable_name] = "number"
                if isinstance(inp,str):
                    vartypes[variable_name] = "string"
                if isinstance(inp,any):
                    vartypes[variable_name] = "any"
                if isinstance(inp,bool):
                    vartypes[variable_name] = "boolean"
                else:
                    print("{ RuntimeError: type not avalable or type does not exist }")
                
                
                
                if verb == True:
                    print("{ RuntimeValue: " + str(variable_name) + " -> " + str(variable_value) + " }")
                else:
                    pass
                print(g_variables)
                return str(variable_name)+" = "+str(variable_value)
        
        elif inp.startswith("let"):
            dinp = inp.replace("let ","")
            dinp = inp.replace(":","")
            dinp = inp.replace("->","")
            parts = inp.split(" ")
            "i,number"
            ditems = str(types.items())
            ditems = ditems.replace("[","")
            ditems = ditems.replace("]","")
            ditems = ditems.replace("(","")
            ditems = ditems.replace(")","")
            ditems = ditems.replace("'","")
            ditems = ditems.replace(",","")
            
            if ditems not in dinp:
                variables[parts[0]] = parts[1]
            else:
                vartypes[parts[0]] = parts[1]
                print(vartypes)
            
            
            
        
        elif inp.startswith("type"):
            inp = inp.replace("type","")
            inp = inp.replace("->","")
            inp.replace("  "," ")
            typename,typevalue = inp.split(" ")
            if "|" in inp:
                typeparts = typevalue.split("|")
                types[typename] = [typeparts]
            types[typename] = typevalue
            if verb == True:
                print("{ RuntimeValue: new type: '"+str(typename)+"' -> "+str(typevalue)+" }")
            else:
                pass
            
            return str(typename)+" = "+str(typevalue)
            
        elif inp.lower().startswith == "while (true)":
            try:
                inp = inp.replace("while (true)","")
                inp = inp.replace(" ","")
                inp = inp.replace("{","")
                inp = inp.replace("}","")
                
                return """while True:
                main(inp)"""
                
                while True:
                    main(inp)
                    
            except Exception:
                print("{ RuntimeError: expected expression }")
            
        
        elif inp.lower().startswith == "while":
            try:
                inp = inp.replace("while","")
                inp = inp.replace("(","")
                inp = inp.replace(")","")
                inp = inp.replace(" ","")
                inp = inp.replace("{","")
                inp = inp.replace("}","")
                wh = inp.split()
                cond = wh[1]
                val = wh[2]

                return """while cond:
                    main(val)"""
                while cond:
                    main(val)
            except:
                print("{ RuntimeError: invalid syntax. }")
        
        elif inp.lower().startswith == "if":
            try:
                inp = inp.replace("if","")
                inp = inp.replace("(","")
                inp = inp.replace(")","")
                inp = inp.replace(" ","")
                inp = inp.replace("{","")
                inp = inp.replace("}","")
                wh = inp.split()
                cond = wh[1]
                val = wh[2]

                return """if cond:
                    main(val)"""
                    
                if cond:
                    main(val)
                    
                
            except Exception:
                print("{ RuntimeError: expected expression }")
            
                
        elif inp.lower().startswith == "for (;;)":
            try:
                inp = inp.replace("for (;;)","")
                inp = inp.replace(" ","")
                inp = inp.replace("{","")
                inp = inp.replace("}","")
                return """while True:
                main(inp)"""
                
                while True:
                    main(inp)
                    
            except Exception:
                print("{ RuntimeError: expected expression }")
            
        
        elif inp.lower().startswith == "!":
            inp = inp.replace("!","")
            os.system(inp)
            return "os.system(inp)"
            
        
        elif "const" in inp:
            return const_creator()
            const_creator()
        elif "interface" in inp:
            return intr()
            intr()
        
        elif "export" in inp:
            parts = inp[8:].strip("()").split(",")  # Remove "export: " and parentheses
            if len(parts) != 2:
                print("{ RuntimeError: invalid export format. Please follow 'export: (<name>,<value>)' }")
            name, value = parts
            return export(name.strip(), value.strip())
            export(name.strip(), value.strip())
        
            
        elif inp.startswith("//"):
            inp.replace("//")
            pass
            return f"#{inp}"
            
        if inp.startswith == "source -> <_ioSource>":
            io = 1
            if md == True:
                print("{ RuntimeValue: input-output library imported }")
            else:
                pass
            
        if "source ->" in inp and ".rh" in inp:
            inp.replace("source ->","")
            print("dg done")
            inp = inp.replace(" ","")
            inp = inp.replace("<","")
            inp = inp.replace(">","")
            inp = inp.replace(".//","./")
            inp = inp.replace("..//","../")
            inp = inp.replace("//","/")
            print(inp)
            
            fileh = open(inp,"r")
            main(fileh)
            fileh.close()
        
        
                    
        
        if inp.startswith == "import * as _ioSource from <_ioSource>":
            io = 1
            print("{ ModuleRV: input-output library imported }")
            
        elif io == 1:
            if inp.startswith == "_io.TextIOWrapper":
                parts = inp.split("(")
                if len(parts) not in (3, 4) or parts[0].lower() != "_io.TextIOWrapper":
                    print("{ RuntimeError: invalid command format. Use 'textwrapper(<operation> | <path> | [<new file data>])' }")

                operation, filepath = parts[1].strip().split("|")
                filepath = filepath.strip()[:-1]  # Remove trailing ')'

                if operation.lower() == "read":
                    try:
                        wrapper = TextWrapper(filepath)
                        return """for line in wrapper:
                            print(line)"""
                        for line in wrapper:
                            print(line)
                    except FileNotFoundError:
                        print("{ RuntimeError: File not found! }")
                elif operation.lower() == "write":
                    if len(parts) == 4:  # Check if new data is provided
                        data_to_write = parts[2].strip()  # Extract data from command
                        return "data_to_write = parts[2].strip()"
                    try:
                        wrapper = TextWrapper(filepath)
                        wrapper.write(data_to_write + "\n")  # Add newline for clarity
                        return '_io.TextIOWrapper.write(data_to_write + "\n")'
                        if verb == True:
                            print("{ RuntimeValue: Data written to '"+str(filepath)+"'. }")
                        else:
                            pass
                    except FileNotFoundError:
                        print(f"error: File '"+str(filepath)+"' not found. Creating a new file.")
                        wrapper = TextWrapper(filepath)
                        wrapper.write(data_to_write + "\n")
                        if verb == True:
                            print("{ RuntimeValue: Data written to new file -> '"+str(filepath)+"'. }")
                        else:
                            pass
                 
                elif operation.lower() == "wb":
                    if len(parts) == 4:  # Check if new data is provided
                        data_to_write = parts[2].strip()  # Extract data from command
                    try:
                        wrapper = TextWrapper(filepath)
                        wrapper.writebin(data_to_write + "\n")  # Add newline for clarity
                        if verb == True:
                            print("{ RuntimeValue: binary Data written to '"+str(filepath)+"'. }")
                        else:
                            pass
                    except FileNotFoundError:
                        print(f"error: File '"+str(filepath)+"' not found. Creating a new file.")
                        wrapper = TextWrapper(filepath)
                        wrapper.write(data_to_write + "\n")
                        if verb == True:
                            print("{ RuntimeValue: binary Data written to new file -> '"+str(filepath)+"'. }")
                        else:
                            pass
                       
                elif operation.lower() == "rb":
                    try:
                        wrapper = TextWrapper(filepath)
                        wrapper.readlnbin()
                    except FileNotFoundError:
                        print("{ RuntimeError: File not found! }")
                else:
                    print("{ RuntimeError: Unsupported operation. Currently only 'read','rb','write' and 'wb' are supported. }")
                

        if inp.lower().startswith("namespace"):
            result = handle_input(inp)
            if result:
                print(result)
                
        elif io == 1:
            if inp.lower().startswith("_io.BytesIO"):
                inp = inp.replace(")","")
                inp.replace("(","")
                inp.replace("[","")
                inp.replace("]","")
                inp.replace("BytesIO","")
                if "]" and "[" in inp:
                    inp = inp.replace(")","")
                    inp = inp.replace("(","")
                    inp = inp.replace("[","")
                    inp = inp.replace("]","")
                    opn = inp.replace("_io.BytesIO","")
                    inp = inp.replace("_io.BytesIO","")
                    Bio = BytesIO()
                    bio(inp)
                if ".close()" in inp:
                    Bio = BytesIO()
                    Bio.close()
                Bio = BytesIO()
                bio(inp)
                                
        elif any(op in inp for op in ["==", "!=", ">", "<","<=", ">="]):
            result = compare_expression(inp)
            if verb == True:
                print("{ RuntimeValue: "+str(inp)+" -> "+str(result)+" }")
            else:
                pass
            
                    
        
        
            
        elif io == 1:
            my_file.handle_input()  # Start accepting inps
                
        elif inp == "exit(0);":  # Separate check for "exit"
            exit(0)
        elif inp == "exit(1);":  # Separate check for "exit"
            exit(0)
        elif inp == "exit();":  # Separate check for "exit"
            exit()
        elif inp == "clear();":
            os.system('cls' if os.name == 'nt' else 'clear')
            print("RuffleScript Notebook ")
            print("\nType `help();` for more information")
           
         
        elif inp == "help();":
            print("\nRuffleScript Command handbook")
            print("-----------------------------\n")
            print("source  -  command to import modules (eg. source -> <_ioSource> )")
            print("var  -  creates variable usable in the program (eg. var myvar -> 'variable text')")
            print("typeface  -  prints plain text (non verbose) to the screen (eg. typeface('ruffle wrote this!') )")
            print("return  -  returns input given (eg. return 'text here')")
            print("for(;;){-}  -  creates a forever loop (eg. for(;;) {retrun 'forever!'} )")
            print("while  -  while loop for program (eg. while (true) {retrun 'heh'} )")
            print("namespaces  -  can create namespaces in your program that are accesable using the command (eg. namespaces(rufflespace) | write('ruffle wrote this!') )")
            print("if  -  creates an if loop fo the program to read (eg. if (1==1) {return 'heh'})")
            print("promptSync  -  asks a prompt in the program (eg. var inp -> promptSync('how old are you?: ') )")
            print("prompt  -  asks for a prompt (does not support variables) (eg. prompt('hello! ') )")
            print("interface  -  makes an interface containing let blocks (eg. interface ruffle {let i: 3; let h: 4})")
            print("exit();  -  exits program (eg. exit(); )")
            print("clear();  -  clears the terminal, freeing space (eg. clear(); )")
            print("//  -  comments line (eg. // this line is commented!)")
            print("\n_ioSource Commands - (can only be used if _ioSource is imported)")
            print("-----------------------------------------------------------------\n")
            print("_io.TextIOWrapper  -  can acess and edit files (eg. _io.TextIOWrapper(write | ./text.txt | 'ruffle wrote this!'))")
            print("_io.IOBase  -  can write lines to the buffer and get their value (eg. _io.IOBase.write('ruffle wrote this!')  -  _io.IOBase.read() )")
            print("_io.BytesIO  -  gets binary data (eg. _io.BytesIO(_io.TextIOWrapper(wb | ./text.txt | 'ruffle wrote this!')[0:10] ) )")
            print("\n")
            
            
            
        else:
            if inp != "":
                print("{ RuntimeError: unknown command '"+inp+"' }")
        
        
                
                
        
    except EOFError:
        print("{ RuntimeError: Beyond EOF -> EOF }")
    except KeyboardInterrupt as e:
        print("\n{ KeyboardInterrupt: "+str(e)+" }")
        exit(0)
    except SyntaxError as e:
        print("{ RuntimeError: invalid syntax'"+str(e)+"' }")
    except SystemError as e:
        print(f"{bbr} system error: {e} {br}")
    except MemoryError:
        print("{ RamError: Cannot allocate memory }")
    except RuntimeError as e:
        print(f"{bbr} {Runtime_error}: {e} {br}")
    except EnvironmentError as e:
        print("{ EnvironmentError: "+str(e)+" }")
    
        
def mainf(inp):
    main(inp)
if __name__ == "__main__":
    
    # file interpreter
    if len(sys.argv) > 1:
        if sys.argv[1] == "":
            nb = 0
            file = sys.argv[1]
            with open(file,"r") as f:
                info = f.read().rstrip('\n')
                tcom = info.split(" ")
            for item in tcom:
                mainf(item)
        if sys.argv[1] == "--init":
            f = open("rsconfig.json","w")
            f.write("""{
    "RuntimeLineSuggestion": "on", // on|off
    "moduleRuntimeValue": "off", // on|off
    "verbose": "false" // true|false
}""")
            print("Created 'rsconfig.json' file.")
                
    elif len(sys.argv) > 1 and sys.argv[1] == "--about":
        print("""\n
              
**********************************************************************
** Rufflescript Developer Notebook & enviroment (v1.6)
** using .REL architecture - [Runtime . Evaluation . Language]
**********************************************************************

""")

    elif sys.argv[1] == "--update":
         if platform.system == 'Windows':
              os.system('del "RuffleScript.py"')
              os.system("cd /")
              os.system("git clone https://github.com/PuppyStudios1/RuffleScript.git")
         else:
              os.system("sudo rm -rf RuffleScript.py")
              os.system("cd /")
              os.system("git clone https://github.com/PuppyStudios1/RuffleScript.git")
         
    # else, rufflescript notebook
    else:
        nb = 1
        os.system('cls' if os.name == 'nt' else 'clear')
        print(logo)
        print("RuffleScript Notebook")
        print("\nType `help();` for more information")
        
        while True:
            main(inp)
            
            
