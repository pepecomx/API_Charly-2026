from multiprocessing import cpu_count

# Socket Path
bind = 'unix:/home/ec2-user/SERVICOS/API_charly/gunicorn.sock'

# Worker Options
workers = cpu_count() + 1
worker_class = 'uvicorn.workers.UvicornWorker'

# Logging Options
loglevel = 'debug'
accesslog = '/home/ec2-user/SERVICOS/API_charly/access_log'
errorlog =  '/home/ec2-user/SERVICOS/API_charly/error_log'

