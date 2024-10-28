#!/bin/bash

# dag 정보와 task 정보를 Jinja template으로 불러올 수 있습니다.
echo "{{ dag }}, {{ task }}"

# dag file에서 전달해 준 test 파라미터는 다음과 같이 쓸 수 있습니다.
echo "{{ params.test }} {{ ds }}"

# execution_date를 표현합니다.
echo "execution_date : {{ execution_date }}"
echo "ds: {{ds}}"

# macros를 이용하여 format과 날짜 조작이 가능합니다.
echo "the day after tommorow with no dash format"
echo "{{ macros.ds_format(macros.ds_add(ds, days=2),'%Y-%m-%d', '%Y%m%d') }}"

# for, if 예제입니다.
{% for i in range(3) %}
        echo "{{ i }} {{ ds }}"
  {% if i%2 == 0  %}
                echo "{{ ds_nodash }}"
  {% endif %}
{% endfor %}