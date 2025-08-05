# clean up the existing files and set up the start portfolio.
# reset.py

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
import json


# More sybol slug mapping could be added in the file in the future.
def load_symbol_slug_mapping_from_file(
	filepath='base_workflow/data/symbol_slug_mapping/symbol_slug_mapping.json',
):
	path = Path(filepath)
	if not path.exists():
		raise FileNotFoundError(f'Slug mapping file not found: {filepath}')
	with open(path, 'r') as f:
		mapping = json.load(f)
	return mapping


def reset_output(folder_path: str, force: bool = False):
	path = Path(folder_path)

	if not path.exists():
		print(f"The folder '{folder_path}' does not exist.")
		return

	if not force:
		confirm = input(f"Are you sure you want to delete '{folder_path}'? [y/N]: ")
		if confirm.lower() != 'y':
			print('Operation cancelled.')
			return

	try:
		shutil.rmtree(path)
		print(f'Successfully deleted the folder: {folder_path}')
	except Exception as e:
		print(f'Failed to delete folder: {e}')


def log_initial_capital(slug: str, remaining_dollar: float):
	"""
	Log only timestamp, slug, and remaining_dollar into the trades table.
	Other fields remain 0.
	"""
	db_path = Path(f'base_workflow/outputs/{slug}_trades.db')
	db_path.parent.mkdir(parents=True, exist_ok=True)
	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()

	# Ensure the full trades table exists
	cursor.execute(
		"""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            action TEXT,
            slug TEXT,
            amount REAL,
            price REAL,
            remaining_dollar REAL
        )
        """
	)

	# Insert minimal capital info
	timestamp = datetime.utcnow().isoformat()
	cursor.execute(
		'INSERT INTO trades (timestamp, slug, amount, remaining_dollar) VALUES (?, ?, 0.0, ?)',
		(timestamp, slug, remaining_dollar),
	)

	conn.commit()
	conn.close()


def main():
	"""
	Reset the output folder and log initial capital for each token.
	Tokens need to be hand written to tokens list.
	Each token will be given an initial capital of 1,000,000 USD.
	Together, the total initial capital is 1,000,000 USD * tokens number.
	"""
	tokens = [
		'BTC',
		'ETH',
		'PEPE',
		'DOGE',
		'USDT',
	]
	initial_capital = 1000000  # average capital per token in USD, total initial capital * tokens number.
	parser = argparse.ArgumentParser(description='Delete the output folder')
	parser.add_argument(
		'--path',
		type=str,
		default='base_workflow/outputs',
		help='Path to the folder to delete (default: base_workflow/outputs)',
	)
	parser.add_argument(
		'--force', action='store_true', help='Delete without confirmation'
	)
	parser.add_argument(
		'--capital',
		type=float,
		default=initial_capital,
		help='Initial capital in USD (default: 1000000)',  # total capital 5000000
	)

	args = parser.parse_args()
	reset_output(args.path, args.force)
	symbol_to_slug = load_symbol_slug_mapping_from_file()
	for token in tokens:
		slug = symbol_to_slug.get(token.upper())
		if slug:
			log_initial_capital(slug, args.capital)
		else:
			print(
				f"Warning: No slug found for token '{token}'. Skipping initial capital logging."
			)


if __name__ == '__main__':
	main()
