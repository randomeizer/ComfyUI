

import random

import comfy.parse
from comfy.parse import ParseError

class LogicError(Exception):
	# something that shouldn't be possible occurred in the code
	# not the user's fault
	pass


def translate_choices(text, seed=0):
	'''
	Parses the text, translating "{A|B|C}" choices into a single choice.
	An option is chosen randomly from the available options.
	For example: "a {green|red|blue} ball on a {wooden|metal} bench" might expand to "a red ball on a wooden bench".
	Nesting choices is supported, so 
	"a woman wearing a {{lavish|garish|expensive|stylish|} {red|brown|blue|} dress|{sexy|realistic|} {police|nurse|maid} uniform|{black leather|wooly|thick} coat}"
	could expand to
	"a woman wearing a stylish brown dress".
	All random choices are governed by the supplied random seed value, ensuring repeatability.
	You can use a single PrimitiveNode with an INT value, and connect that to the CLIPTextEncode node and the KSampler node in a typical Stable Diffusion 1.5 workflow, for example.
	
	Notes:
		* this function must correctly support valid inputs
		* for invalid inputs:
			* raise an error if that's supported cleanly enough in the system
			* otherwise, return the original input as the output, and issue a warning to stdout or stderr if that's acceptable in the system
		* must preserve escaped metacharacters for the prompt weight parsing
	'''
	
	# the user will be escaping for both this processing (using curly braces) and the weight processing (using round parentheses)
	# from their perspective, they will need to escape literal data like this to cover both sets of processing:
	# { -> \{
	# } -> \}
	# | -> \|
	# \ -> \\
	# ( -> \(
	# ) -> \)
	
	def parse_choice(input):
		options = []
		while True:
			options.append(parse_text_with_choices(input))
			if 0: pass
			elif m := input.match(r'\|'):
				# loop around for another choice
				pass
			elif m := input.match(r'\}'):
				break
			else:
				raise ParseError(input, f"Expected '|' or '}}' after choice text")
		
		# choose one of the options
		text = rng.choice(options)
		return text
	
	def parse_text_with_choices(input):
		out = []
		
		while True:
			if 0: pass
			elif m := input.match(r'\\'): # \
				if 0: pass
				elif m := input.match(r'[\{\|\}\/]'):
					# escaping a metacharacter to make it literal
					out.append(m.group(0)) # output literal character
				elif m := input.match(r'.'):
					# by passing through non-native or unrecognised escape codes without change, we support clean combiniation of multiple parsing phases
					# without forcing the user to add additional escaping for each phase
					out.append(f'\\{m.group(0)}')
				else:
					raise ParseError(input, f'Unexpected end of input after backslash')
			elif m := input.match(r'\{'): # {
				# choice
				chosen_text = parse_choice(input)
				out.append(chosen_text)
			elif m := input.match(r'\/'): # /
				# C-style block "/* */" and line "//" comments
				if 0: pass
				elif m := input.match(r'\/'): # /
					# line comment
					if not input.match(r'.*?(?:\n|$)'):
						raise ParseError(input, f"Failed to find end of comment")
					out.append('\n')
				elif m := input.match(r'\*'): # /
					# block comment
					if not input.match(r'.*?\*\/'):
						raise ParseError(input, f"Unterminated comment")
					out.append(' ')
				else:
					# it was a literal /, not a comment after all
					out.append('/');
			elif m := input.match(r'[^\\\{\}\|\/]+'): # 1 or more non-metacharacters
				out.append(m.group(0))
			else:
				# didn't match \, {, / or non-metacharacters
				# must be either |, } or end of input
				break
		
		return ''.join(out)
	
	# init our local random number generator
	rng = random.Random(seed)
	
	try:
		input = comfy.parse.Cursor(text)
		out = parse_text_with_choices(input)
		if not input.match(r'$'):
			raise ParseError(input, f'Failed to parse up to the end of the prompt text')
		
		return out
	except (ParseError, LogicError) as e:
		# alternative: re-throw the error
		stdout.write(f'Error parsing prompt: {e}');
		return text
