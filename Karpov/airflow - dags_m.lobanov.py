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

'''
1. Прочитайте csv файл, который находится по этой ссылке, при помощи библиотеки pandas

https://docs.google.com/spreadsheets/d/e/2PACX-1vR-ti6Su94955DZ4Tky8EbwifpgZf_dTjpBdiVH0Ukhsq94jZdqoHuUytZsFZKfwpXEUCKRFteJRc9P/pub?gid=889004448&single=true&output=csv
2. В данных вы найдете информацию о событиях, которые произошли с объявлением 121288 за два дня. Рассчитайте следующие метрики в разрезе каждого дня:

количество показов
количество кликов
CTR 
сумма потраченных денег 
То есть для каждой метрики у вас должно получиться два числа - за 2019-04-01 и 2019-04-02

Рассчитать сумму потраченных денег можно по следующей формуле - разделите значение из колонки ad_cost на 1000 и умножьте на количество показов объявления

3. Теперь найдите процентную разницу между этими метриками. То есть найдите, насколько процентов каждая метрика увеличилась/уменьшилась 2 апреля по сравнению с 1 апреля

4. Создайте текстовый файл, в котором будет собрана информация о том, какие метрики наблюдаются 2 апреля (представьте, что 2 апреля это сегодня, условно, вы отправляете отчет за сегодня, сравнивая данные со вчера), а также, на сколько процентов они уменьшились по сравнению со вчера. То есть в текстовом файле должен быть список метрик, их значения 2 апреля и процентное отличие от 1 апреля. Вариант текстового отчета:

Отчет по объявлению 121288 за 2 апреля
Траты: Х рублей (Y%)
Показы: X (Y%)
Клики: X (-Y%)
CTR: X (-Y%)

5. Отправьте получившийся текст к себе в личные сообщения во ВКонтакте в виде сообщения со сводкой метрик

6. Все предыдущие шаги оформите в виде исполняемого скрипта (скриптов) и скрипта для DAG'а, в котором при помощи BashOperator'а (или других операторов на ваше усмотрение) будет вызываться исполняемый скрипт (скрипты)

7. В расписании для крона укажите каждый понедельник в 12 утра. Так, чтобы ваш скрипт с расчётом дневных метрик отправлялся вам в личку каждый понедельник в 12 утра из Airflow
'''
