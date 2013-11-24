import os
import subprocess
import re
import fileinput
import shutil
import errno
import tempfile
import pprint

set_client_field = re.compile(r'(?P<mcpbot_command>scf) (?P<searge_name>\w+) (?P<semantic_name>\w+)( (?P<description>.+))?', flags=re.IGNORECASE)
set_client_method = re.compile(r'(?P<mcpbot_command>scm) (?P<searge_name>\w+) (?P<semantic_name>\w+)( (?P<description>.+))?', flags=re.IGNORECASE)
set_server_field = re.compile(r'(?P<mcpbot_command>ssf) (?P<searge_name>\w+) (?P<semantic_name>\w+)( (?P<description>.+))?', flags=re.IGNORECASE)
set_server_method = re.compile(r'(?P<mcpbot_command>ssm) (?P<searge_name>\w+) (?P<semantic_name>\w+)( (?P<description>.+))?', flags=re.IGNORECASE)

mcpbot_url = 'http://mcpold.ocean-labs.de/index.php/MCPBot'

def show_help():
	print('Usage: `scf/scm/ssf/ssm <searge_name> <semantic_name> [description]`.')
	print('See %s for more details' % mcpbot_url)
	print('end: exit the script')
	print('h: show help')

def process_command(data, src_dir, mcp_live_dir, output_file):
	mcpbot_commands_file = os.path.join(mcp_live_dir, output_file)
	with open(mcpbot_commands_file, 'a') as f:
		f.write('{0} {1} {2}'.format(data['mcpbot_command'], data['searge_name'], data['semantic_name']) + (' ' + data['description'] if data['description'] else '') + '\n')

	files = grep_search(src_dir, data['searge_name'])
	for each in files:
		backup_file(mcp_live_dir, each)
		tmp = tempfile.NamedTemporaryFile(delete=False)
		with open(each) as src:
			i = 1
			for line in src:
				if data['searge_name'] in line:
					print('In line {0} of {1}:'.format(i, each))
					print(line)
					yes = console_readline('Replace?', ('y', 'n'))
					if yes != 'y':
						print('Skipping this line.')
						tmp.write(line)
					else:
						print('Wrote replacement: %s' % line.replace(data['searge_name'], data['semantic_name']))
						tmp.write(line.replace(data['searge_name'], data['semantic_name']))
				else:
					tmp.write(line)
				i += 1
		tmp.close()
		os.remove(each)
		shutil.move(tmp.name, each)

def process_line(user_cmd, src_dir, mcp_live_dir, output_file):
	match = set_client_field.match(user_cmd) or set_client_method.match(user_cmd) or set_server_field.match(user_cmd) or set_server_method.match(user_cmd)
	if match is None:
		print('Invalid command.')
		show_help()
		return
	data = {
		'mcpbot_command': match.group('mcpbot_command'),
		'searge_name': match.group('searge_name'),
		'semantic_name': match.group('semantic_name'),
		'description': match.group('description')
	}

	print('Command: %s' % expand_mcpbot_command(data['mcpbot_command']))
	print('Searge name: %s' % data['searge_name'])
	print('Semantic name: %s' % data['semantic_name'])
	print('Description: %s' % (data['description'] if data['description'] else '(None given.)'))

	yes = console_readline('Is this okay?', ('y', 'n'))
	if yes != 'y':
		print('Aborting.')
		return

	process_command(data, src_dir, mcp_live_dir, output_file)

def main():
	src_dir = './src/'
	mcp_live_dir = './mcp-live/'
	mcpbot_commands_file = 'mcpbot_commands.txt'

	mkdir_p(mcp_live_dir)

	touch(os.path.join(mcp_live_dir, mcpbot_commands_file))

	if not os.path.exists(src_dir):
		print('Source folder not found. Exiting')
		return

	print('Type \'h\' for help.')

	while True:
		user_cmd = console_readline('> ')
		if user_cmd == 'end':
			break
		elif user_cmd in ('h', 'help', '?'):
			show_help()
		else:
			process_line(user_cmd, src_dir, mcp_live_dir, mcpbot_commands_file)
		print('')
	print('Done.')

### Uninteresting functions
def console_readline(prompt='', valid_set=None):
	if valid_set is None:
		return raw_input(prompt)
	else:
		prompt = prompt + ' [' + '/'.join(map(lambda x: str(x), valid_set)) + ']: '
		while True:
			user_input = raw_input(prompt)
			if user_input in valid_set:
				return user_input
			print('Invalid input. Enter one of %s.' % str(valid_set))

def grep_search(basedir, needle):
	files = subprocess.check_output(['grep', '-ril', needle, basedir])
	return files.decode('utf-8').split('\n')[:-1]

def expand_mcpbot_command(cmd):
	substitutions = {
		'c': 'client',
		's': 'server',
		'f': 'field',
		'm': 'method',
	}
	return ' '.join(['set' if cmd[0] == 's' else 'get'] + map(lambda ch: substitutions[ch], cmd[1:]))

def mkdir_p(path):
	try:
		os.makedirs(path)
	except OSError as ex:
		if ex.errno == errno.EEXIST and os.path.isdir(path):
			pass
		else:
			raise

def touch(filepath):
	with file(filepath, 'a'):
		os.utime(filepath, None)

def backup_file(backup_location, filepath):
	backup = os.path.join(backup_location, filepath)
	mkdir_p(backup)
	if not os.path.exists(backup):
		shutil.copyfile(filepath, backup)
	return backup

if __name__ == '__main__':
	main()