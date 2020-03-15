import boto3
import json
from boto3.dynamodb.conditions import Key, Attr
from flask import Flask, redirect, url_for, request, render_template, jsonify

app = Flask(__name__)
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1', endpoint_url="https://dynamodb.eu-west-1.amazonaws.com")
table = dynamodb.Table('playpit-labs-stats')

@app.route('/<name>/<training>',methods = ['POST', 'GET'])
def success(name, training):
    structure_dict = {}
    training_list = []
    response = table.scan(
        FilterExpression=Attr('student').eq(name)
    )
    items = response['Items']

    if training:
        training_list.append('siarhei_beliakou/playpit-labs-' + training + '/master')
    else:
        # Add all training list
        for i in items:
            training_list.append(i.get('training'))
        training_list = set(training_list) # full training list

    for i in training_list:
        structure_dict[i] = {}
    # Add all module for each training
    for tn in structure_dict.keys():
        module_list = []
        module_dict = {}
        for i in items:
            if i.get('training') == tn:
                module_list.append(i.get('module'))
        module_list = set(module_list) ## for training
        for i in module_list:
            module_dict[i] = {}
        structure_dict[tn] = module_dict

    # Add all task for each module for each training
    for tn in structure_dict.keys():
        for mn in structure_dict[tn]:
            task_dict = {}
            task_list = []
            for i in items:
                if i.get('module') == mn and i.get('training') == tn:
                    task_list.append(i.get('task'))
            taks_list = set(task_list) ## for training
            for i in task_list:
                task_dict[i] = {}
            structure_dict[tn][mn] = task_dict

    # Add max score for each task
    for tn in structure_dict.keys():
        for mn in structure_dict[tn]:
            for ti in structure_dict[tn][mn]:
                score_list = []
                for i in items:
                    if i.get('module') == mn and i.get('training') == tn and i.get('task') == ti:
                        score_list.append(int(i.get('score')))
                score_list = max(score_list)
                structure_dict[tn][mn][ti] = score_list
    
    # Add max task value for each module
    for tn in structure_dict.keys():
        for mn in structure_dict[tn]:
            for i in items:
                if i.get('module') == mn and i.get('training') == tn:
                    task_max = int(i.get('task_max'))
            structure_dict[tn][mn]['task_max'] = task_max - 1

    module_list = sorted(module_list)
    training_name_stat = training_list[0]

    out_put_json = {name: {}}
    result_dict = {}
    for m in module_list:
        list_score_tasks = []
        for ti in structure_dict[training_name_stat][m]:
            if ti != 'task_max':
                list_score_tasks.append(structure_dict[training_name_stat][m][ti])
        to_table = str(int(sum(list_score_tasks)/structure_dict[training_name_stat][m]['task_max']))
        result_dict[m] = to_table
    out_put_json[name] = result_dict
    to_send = out_put_json
    return jsonify(to_send)

@app.route('/manual',methods = ['POST', 'GET'])
def manual():
    if request.method == 'POST':
       student = request.form['student']
       training = request.form['training']
       return redirect(url_for('success', name = student, training = training))
    else:
       student = request.args.get('student')
       training = request.form['training']
       return redirect(url_for('success', name = student, training = training))

@app.route('/ui',methods = ['POST', 'GET'])
def root():
    return app.send_static_file('index.html')

@app.route('/all_student',methods = ['POST', 'GET'])
def all_student():
    response = table.scan()
    items = response['Items']
    list_name = []
    for i in items:
        list_name.append(i.get('student'))
    list_name = set(list_name)
    tbd = list(list_name)
    sout = sorted(tbd)
    return render_template('list.html', name_list=sout)

if __name__ == '__main__':
    app.run(debug=True)