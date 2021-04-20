from airflow import DAG
from airflow.operators import PythonOperator
from datetime import datetime

default_args = {
'owner': 'mlobanov',
'depends_on_past': False,
'start_date': datetime(2021, 4, 10),
'retries': 0   }
    
dag = DAG('Send_vk_report', default_args = default_args, schedule_interval = '00 12 * * 1')


def send_vk_report():

    import pandas as pd
    import numpy as np
    import vk_api

    df = pd.read_csv('https://docs.google.com/spreadsheets/d/e/2PACX-1vR-ti6Su94955DZ4Tky8EbwifpgZf_dTjpBdiVH0Ukhsq94jZdqoHuUytZsFZKfwpXEUCKRFteJRc9P/pub?gid=889004448&single=true&output=csv')

    ad_cost = df.ad_cost[0]

    df = df.groupby(['date', 'event'], as_index=False)['ad_id'].count() \
      .pivot(index='date', columns='event', values='ad_id').reset_index()

    df['CTR'] = df['click'] / df['view']
    df['Total_cost'] = np.round((ad_cost / 1000) * df['view'], 2)

    click_diff = np.round((((df.click[1] - df.click[0]) / df.click[0]) * 100), 2)
    view_diff = np.round((((df.view[1] - df.view[0]) / df.view[0]) * 100), 2)
    CTR_diff = np.round((((df.CTR[1] - df.CTR[0]) / df.CTR[0]) * 100), 2)
    Total_cost_diff = np.round((((df.Total_cost[1] - df.Total_cost[0]) / df.Total_cost[0]) * 100), 2)

    message = f'''Отчет по объявлению 121288 за 2 апреля
    Траты: {df.Total_cost[1]} рублей ({Total_cost_diff} %)
    Показы: {df.view[1]} ({view_diff} %)
    Клики: {df.click[1]} ({click_diff} %)
    CTR: {df.CTR[1]} ({CTR_diff} %)'''

    token = '66117ac9424a6b67d404d24a1cb0fcfec6a150abeb21fb62b1edea6ddda943c35975ca53f7084347b094c'

    vk_session = vk_api.VkApi(token=token)
    vk = vk_session.get_api()

    vk.messages.send(
        user_id='7768141',
        random_id=2,
        message=message)
    
t1 = PythonOperator(task_id='send_vk_report_task', python_callable=send_vk_report, dag=dag)

