# 处理相应的异常，并标识cmd
# import data_info as data
# import kbreak.data_info as data
# from kbreak import data_info as data
from forms.fbreak import data_info as data


# 返回True表示事件已经被处理
def wrapper_to_post(_type, content):
    return {'type': _type, 'payload': content}


def handle_it(exception_details):
    # print(exception_details)
    access_violation_flag = False
    if 'access-violation' == exception_details['type']:
        memory = exception_details['memory']
        if int(memory['address'], 16) in range(data.break_point_info['break_addr'],
                                               data.break_point_info['break_addr'] + data.break_point_info[
                                                   'break_len']):
            # 命中断点,展示内容
            data.break_point_info['current_pc'] = int(exception_details['address'], 16)
            data.break_point_info['current_lr'] = int(exception_details['context']["lr"], 16)
            data.break_point_info['cmd'] = 3
            access_violation_flag = True
        elif int(memory['address'], 16) in range(data.break_point_info['break_page_info'][0],
                                                 data.break_point_info['break_page_info'][0] + data.proc_info[
                                                     'pagesize']):
            # 没有命中断点，但是命中下断点的页面
            data.break_point_info['current_pc'] = int(exception_details['address'], 16)
            data.break_point_info['current_lr'] = int(exception_details['context']["lr"], 16)
            data.break_point_info['cmd'] = 1
            access_violation_flag = True
        else:
            # 不是此断点触发的异常
            print('ignore the access-violation exception...')
            data.break_point_info['cmd'] = 100
            access_violation_flag = True
    if access_violation_flag:
        data.rpc.api._script.post(wrapper_to_post('exception_ret', data.break_point_info))
        return
    if 'breakpoint' == exception_details['type']:
        # 如果列表为空则不是此软断点
        if 0 == len(data.soft_breakpoint_runtime):
            data.rpc.api._script.post(wrapper_to_post('exception_ret', {'info': 'breakpoint', 'cmd': 100}))
            return
        for index in range(0, len(data.soft_breakpoint_runtime)):
            if int(exception_details['address'], 16) == data.soft_breakpoint_runtime[index]['break_addr'] or int(exception_details['address'], 16)+1 == data.soft_breakpoint_runtime[index]['break_addr']:
                data.soft_breakpoint_runtime[index]['cmd'] = 2
                data.soft_breakpoint_runtime[index]['break_page_info'] = data.break_point_info['break_page_info']
                data.soft_breakpoint_runtime[index]['index'] = index
                data.rpc.api._script.post(wrapper_to_post('exception_ret', data.soft_breakpoint_runtime[index]))
                return
        # 如果没有找到则不是此断点触发的异常
        print('ignore the breakpoint exception...')
        data.soft_breakpoint_runtime['cmd'] = 100
        data.rpc.api._script.post(wrapper_to_post('exception_ret', {'info': 'breakpoint', 'cmd': 100}))
        return


def handle(exception_details):
    return handle_it(exception_details)
    # raise Exception('arch:%s or platform:%s not support' % (data.proc_info['arch'], data.proc_info['platform']))
