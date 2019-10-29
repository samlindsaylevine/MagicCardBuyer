import os
import pathlib
import shutil
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from magiccardbuyer.configuration import Configuration

class WebpageReader:
	"""This utility class lets us isolate our webpage reading in one place;
	furthermore, it lets us optionally cache on disk the results of reading web pages,
	so that if we get partway through a run, we can memoize the results of all our 
	price lookups so that we don't have to repeat them all.
	"""

	cache_dir = "webpage_cache"

	def __init__(self, cache: bool):
		self.cache = cache
		if not cache:
			self._clear_cache()

	@classmethod
	def from_config(cls, config: Configuration):
		return WebpageReader(config.cache)

	def read(self, url: str) -> str:
		if self.cache:
			cached_value = self._load_from_cache(url)
			if cached_value is None:
				page = self._readUrl(url)
				self._persist_in_cache(url, page)
				return page
			else:
				return cached_value
		else:
			return self._readUrl(url)


	def _readUrl(self, url):
		timeoutInSecs = 20
		maxRetries = 5
		for retryCount in range(1, maxRetries):
			try:
				return urllib.request.urlopen(url, timeout=timeoutInSecs).read()
			except (urllib.error.URLError, socket.timeout) as e:
				sys.stderr.write(f"Failed to load URL {url} on attempt {retryCount}: {e}\n")
				# Try again.
		raise IOError("Couldn't load '" + url + "' after " + str(maxRetries) + " attempts!")

	def _load_from_cache(self, url:str):
		try:
			with open(self._cached_filename(url)) as cached_file:
				return cached_file.read()
		except FileNotFoundError:
			return None

	def _persist_in_cache(self, url: str, page: str):
		pathlib.Path(WebpageReader.cache_dir).mkdir(exist_ok = True)
		with open(self._cached_filename(url), "w+b") as cached_file:
			cached_file.write(page)

	def _cached_filename(self, url: str) -> str:
		return f"{WebpageReader.cache_dir}/{url.replace('/', '-')}"

	def _clear_cache(self):
		if os.path.isdir(WebpageReader.cache_dir):
			shutil.rmtree(WebpageReader.cache_dir)



if __name__ == "__main__":
	page = WebpageReader(cache = True).read("http://example.com")
	print(page)