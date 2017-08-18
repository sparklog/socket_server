#-*- coding:utf8 -*-
import select, socket, sys, Queue
import logging
from logging.config import fileConfig

''' socket server  '''

fileConfig('logging_config.ini')
logger = logging.getLogger('cse')


def save_to_db():
    ''' save data to mongo '''
    logger.info("start save_to_db function")
    pass

def parse_data(data):
    logger.info('start parse_data function')
    ''' parse the socket client's data'''
    li = data.split('&')
    if  data.find("900150983cd24fb0d6963f7d28e17f72") == -1: # 判断数据来源是否合法
        logger.warning('unlegal input data ：'+str(data))
        return

    for key in li:
        print key
        write_to_file(key)
    save_to_db()

def write_to_file(data):
    with open('socket_client_data.txt', 'a+') as f:
        f.write(data+"\n")

def start_server():
    ''' start server '''
    BUF_SIZE = 8192
    HOST = '0.0.0.0'
    PORT = 17954
    THREADS = 100
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setblocking(0)
    server.bind((HOST, PORT))
    server.listen(THREADS)
    inputs = [server]
    outputs = []
    message_queues = {}

    while inputs:
        readable, writable, exceptional = select.select(
            inputs, outputs, inputs)
        for s in readable:
            if s is server:
                connection, client_address = s.accept()
                logger.info('Client address is : ' +  str(client_address))
                connection.setblocking(0)
                inputs.append(connection)
                message_queues[connection] = Queue.Queue()
            else:
                try:
                    data = s.recv(BUF_SIZE)
                except Exception,ex:
                    logger.error(ex.message)

                if data:
                    parse_data(str(data).rstrip(''))
                    #print(["".join(str(data).rstrip(''))])
                    message_queues[s].put(data)
                    if s not in outputs:
                        outputs.append(s)
                else:
                    if s in outputs:
                        outputs.remove(s)
                    inputs.remove(s)
                    s.close()
                    del message_queues[s]

        for s in writable:
            try:
                next_msg = message_queues[s].get_nowait()  # 非阻塞获取
            except Queue.Empty:
                logger.info('Output Queue is Empty')
                # g_logFd.writeFormatMsg(g_logFd.LEVEL_INFO, err_msg)
                outputs.remove(s)
            except Exception, e:  # 发送的时候客户端关闭了则会出现writable和readable同时有数据，会出现message_queues的keyerror
                err_msg = "Send Data Error! ErrMsg:%s" % str(e)
                logger.error(err_msg)
                if s in outputs:
                    outputs.remove(s)

            else:
                try:
                    s.send('NOP')
                except Exception,ex:
                    logger.error(ex.message)


        for s in exceptional:
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()
            del message_queues[s]

if __name__ == "__main__":
    start_server()