import os, sys, tokenize, subprocess, re

matcher = re.compile('def .*\(.*\)\:|class .*\(.*\)\:')

source_file = os.path.join(os.getcwd(), '../snickers/main.py')
#proc = subprocess.Popen("egrep 'def|class' {}".format(source_file), stdout=subprocess.PIPE)
#readline = proc.readline

readline = os.popen("egrep 'def|class' {}".format(source_file)).readline
# source_file_handle = open(source_file, 'rb')
# readline = source_file_handle.readline

# Types = type: def, params: [], parent_node: <pointer>
# Types = type: class, children: [], parent_node: <pointer>
module_objects = []

tokens_g = tokenize.tokenize(readline)
look_for = 'class_or_function'
current_node = module_objects
indentation_count = 0

def extract_interesting_lines(string):
    ss = string.split("\n")

def state_append(c_node, obj, current_indentation):
    obj['parent_node'] = c_node
    obj['current_indentation'] = current_indentation
    if type(c_node) == list:
        c_node.append(obj)
    elif type(c_node) == dict:
        if c_node['type'] in ['class', 'def'] and obj['type'] in ['def', 'class']:
            c_node['children'].append(obj)
        elif c_node['type']=='def' and obj['type']=='param':
            c_node['params'].append(obj)
    return obj

def build_tree(tokens, look_for, current_node, dent, current_indentation):
    try:
        token = next(tokens)
    except StopIteration:
        return None
    if tokenize.tok_name[token.type]=='NAME' and token.string=='def':
        if look_for=='class_or_function':
            current_indentation = dent
            look_for = 'function_name'
    elif tokenize.tok_name[token.type]=='NAME' and token.string=='class':
        current_indentation = dent
        obj = {'type': 'class', 'children': []}
        current_node = state_append(current_node, obj, current_indentation)
        look_for = 'class_name'
    elif tokenize.tok_name[token.type]=='NAME':
        if look_for=='param':
            obj = {'type': 'param', 'name': token.string}
            current_node = state_append(current_node, obj, current_indentation)
            look_for = "eq_comma_value_close_param"
        elif look_for=='function_name':
            obj = {'type': 'def', 'params': [], 'children':[], 'name': token.string}
            current_node = state_append(current_node, obj, current_indentation)
            look_for = 'open_param'
        elif look_for=='class_name':
            obj = {'type': 'class', 'children': [], 'name': token.string}
            current_node = state_append(current_node, obj, current_indentation)
            look_for='class_or_function'
        elif look_for=='ignore_param_value':
            look_for = 'eq_comma_value_close_param'
    elif tokenize.tok_name[token.type]=='OP':
        if token.string=='(' and look_for=='open_param':
            look_for = 'param'
        elif look_for == 'eq_comma_value_close_param':
            if token.string == ')':
                look_for = 'class_or_function'
                current_node = current_node['parent_node']
            elif token.string == ',':
                look_for = 'param'
            elif token.string == '=':
                look_for = 'ignore_param_value'
        elif look_for == 'param' and token.string == ')':
            look_for = 'class_or_function'
            current_node = current_node['parent_node']
    elif tokenize.tok_name[token.type]=='INDENT':
        dent += 1
    elif tokenize.tok_name[token.type]=='DEDENT':
        if current_indentation==dent:
            current_node = current_node['parent_node']
        dent -= 1

    build_tree(tokens, look_for, current_node, dent, current_indentation)

def print_tree_struct(tree_struct, indents=0):
    indents_str = "\t"*indents
    if type(tree_struct)==list:
        for item in tree_struct:
            print_tree_struct(item, indents)
    elif tree_struct['type']=='class':
        if 'name' in tree_struct:
            print("{} class {} current_indentation {}".format(indents_str, tree_struct['name'], tree_struct['current_indentation']))
        if 'children' in tree_struct:
            print_tree_struct(tree_struct['children'], indents+1)
    elif tree_struct['type']=='def':
        print("{} function {} ({}) current_indentation {}".format(indents_str, tree_struct['name'], ', '.join([p['name'] for p in tree_struct['params']]), tree_struct['current_indentation']))
        if 'children' in tree_struct:
            print_tree_struct(tree_struct['children'], indents+1)

def print_tree_struct_2(tree_struct):
    if type(tree_struct)==list:
        for item in tree_struct:
            print_tree_struct_2(item)
    else:
        print("\t"*tree_struct['current_indentation'] + ', '.join(["{}: {}".format(k, v) for k,v in tree_struct.items() if k not in ['children', 'parent_node', 'params']]))
        if 'children' in tree_struct and len(tree_struct['children'])!=0:
            print("Children of {}".format(tree_struct.get('name', 'UNKNOWN')))
            print_tree_struct_2(tree_struct['children'])

build_tree(tokens_g, look_for, current_node, indentation_count, 0)
print_tree_struct(module_objects, indents=0)

print_tree_struct_2(module_objects)
