import re
import xml.sax.saxutils as xmlutils

def xml_to_plain_text(xml_string):
   remove_tags = re.compile(r'\s*<.*?>', re.DOTALL | re.UNICODE)
   plain_text = remove_tags.sub('\n', xml_string)
   # run this twice for weird situations where things are double escaped
   plain_text = xmlutils.unescape(plain_text, {'&apos;': "'", '&quot;': '"'})
   plain_text = xmlutils.unescape(plain_text, {'&apos;': "'", '&quot;': '"'})

   return plain_text.strip()


