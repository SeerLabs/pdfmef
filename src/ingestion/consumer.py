import pika, os, time

# from ingestion.csx_ingester import CSXIngesterImpl


def pdf_process_function(msg):
  print(" PDF processing")
  print(" [x] Received " + str(msg))
  print(" PDF processing finished")
  # csx_ingester = CSXIngesterImpl()
  # print(msg)
  # csx_ingester.ingest_paper("/data/sfk5555/ACL_results/")
  # csx_ingester.ingest_batch_parallel("/data/sfk5555/ACL_results/2020072500")
  return

# Access the CLODUAMQP_URL environment variable and parse it (fallback to localhost)
url = os.environ.get('CLOUDAMQP_URL', 'amqp://guest:guest@rabbitmq/%2f')
params = pika.URLParameters(url)
connection = pika.BlockingConnection(params)
channel = connection.channel() # start a channel
channel.queue_declare(queue='extractor') # Declare a queue

# create a function which is called on incoming messages
def callback(ch, method, properties, body):
  print(body)
  pdf_process_function(body)

# set up subscription on the queue
channel.basic_consume('extractor', callback, auto_ack=True)

# start consuming (blocks)
channel.start_consuming()
connection.close()