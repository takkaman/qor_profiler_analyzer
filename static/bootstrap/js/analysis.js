
function switchMetrics(e) {
        var metrics = $(e).attr('id');
        console.log(metrics);
        $("#sqb-switch").text(metrics);
        $(".sqb-summary").css("display","none");
        $(".sqb-chart").css("display","block");
        window.bs_data = [];
        $.each(window.step_qor_info[metrics], function(design_name, value) {
            if (value == "null") {
                return true;
            }
            $.each(value, function(index, qor_data_list) {
                //console.log(qor_data_list[0])
                var dir = encodeURIComponent($("#sqb1-flow-dir").val());
                var pattern = $("#pattern").text().trim();
                var stage = $("#stage").text().trim().toLowerCase().substring(2, 6);
                var reg = /\d+/;
                var prevp = qor_data_list[0].match(reg);
                var crntp = qor_data_list[2].match(reg);
                var mt = "http://"+window.location.host+"/profile_"+ stage + "?mode=flow&compress=1&input_list=" + dir +"&cmd=" + stage +"&active_design=" + design_name
                    +"&active_metrics=undefined&active_pattern=" + pattern + "&prev_d=0&prev_p=" + prevp + "&crnt_d=0&crnt_p="+ crntp ;
                var data_ele = {
                    "design_name": design_name,
                    "step_name": qor_data_list[2],
                    "step_val": qor_data_list[3],
                    "base_name": qor_data_list[0],
                    "base_val": qor_data_list[1],
                    "pct": qor_data_list[4],
                    "link": "<a href='"+ mt +"'>View</a>"
                }
                window.bs_data.push(data_ele)
                //$("#sqb_bs_table").append(trHTML)
            })
            //console.log(design_name)
            //console.log(value)
        });

        var distri_list = getDistriCount(window.bs_data);
        console.log(distri_list);

        myBarChart.config.data.datasets[0].data = distri_list;
        myBarChart.update();
        $('#sqb_bs_table').bootstrapTable('destroy').bootstrapTable({
            //toolbar: '#toolbar',                //工具按钮用哪个容器
            striped: true,                      //是否显示行间隔色
            //cache: false,                       //是否使用缓存，默认为true，所以一般情况下需要设置一下这个属性（*）
            pagination: true,                   //是否显示分页（*）
            sortable: true,                     //是否启用排序
            //sortOrder: "asc",                   //排序方式
            //queryParams: oTableInit.queryParams,//传递参数（*）
            //sidePagination: "server",           //分页方式：client客户端分页，server服务端分页（*）
            pageNumber:1,                       //初始化加载第一页，默认第一页
            pageSize: 50,                       //每页的记录行数（*）
            pageList: [10, 25, 50, 100],        //可供选择的每页的行数（*）
            search: true,
            showColumns: true,
            showExport: true,
            //strictSearch: true,
            //clickToSelect: true,                //是否启用点击选中行
            //height: 460,                        //行高，如果没有设置height属性，表格自动根据记录条数觉得表格高度
            //uniqueId: "id",                     //每一行的唯一标识，一般为主键列
            //cardView: false,                    //是否显示详细视图
            //detailView: false,                   //是否显示父子表
            columns: [{
                field: 'design_name',
                title: 'Design Name',
                sortable: true
            }, {
                field: 'step_name',
                title: 'Step Name',
                sortable: true
            }, {
                field: 'step_val',
                title: 'Step Value',
                sortable: true
            }, {
                field: 'base_name',
                title: 'Base Step',
                sortable: true
            }, {
                field: 'base_val',
                title: 'Base Value',
                sortable: true
            }, {
                field: 'pct',
                title: 'Percentage (%)',
                sortable: true
            },{
                field: 'link',
                title: 'Profile link',
                sortable: true,

            }
            ],
            data: window.bs_data
        });
    }

function switchNewMetrics(e){
    $(".sqb-chart").css("display","none");
    var summary = [];
    for(key in  window.step_qor_info) {
        summary.push([key]);
    }
//                console.log(summary);
    summary_data = [];
    $.each(summary,function(index,dvalue){
        window.bs_data = [];
        $.each(window.step_qor_info[dvalue], function(design_name, value) {
            if (value == "null") {
                return true;
            }
            $.each(value, function(index, qor_data_list) {
                var data_ele = {
                    "pct": qor_data_list[4]
                };
                window.bs_data.push(data_ele);
            })
        });
        var distri_list = getDistriCount(window.bs_data);
        //console.log(distri_list);
        summary_data.push(distri_list);
    });

    $(".sqb-summary").empty();
    $.each(summary,function(index,svalue){
        var newdiv = "<div class='col-md-2'> <div class='panel' style='border-color: #54c7ce;'>"
            +" <div class='panel-heading'>"+svalue+"</div> <canvas id='canvas"+index+"' width='300' height='300'></canvas></div> </div>";
        $(".sqb-summary").append(newdiv);
        var ctx = $("#canvas"+index).get(0).getContext("2d");
        var data3 = {
            labels: ["-100%+", "-100%", "(-100%~-80%]", "(-80%+~-50%]","(-50%~-20%]", "(-20%~-10%]", "(-10%~-0%)", "0%", "(+0%~+10%)", "[+10%~+20%)", "[+20%~+50%)", "[+50%~+80%)", "[+80%~+100%)", "+100%", "+100%+"],
            datasets: [
                {
                    label: "qor distribution",
                    backgroundColor: [
                        'rgba(153, 204, 51, 1)',
                        'rgba(153, 204, 51, 0.9)',
                        'rgba(153, 204, 51, 0.8)',
                        'rgba(153, 204, 51, 0.6)',
                        'rgba(153, 204, 51, 0.5)',
                        'rgba(153, 204, 51, 0.3)',
                        'rgba(153, 204, 51, 0.1)',
                        'rgba(119, 119, 119, 0.2)',
                        'rgba(255, 99, 132, 0.1)',
                        'rgba(255, 99, 132, 0.3)',
                        'rgba(255, 99, 132, 0.5)',
                        'rgba(255, 99, 132, 0.6)',
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(255, 99, 132, 0.9)',
                        'rgba(255, 99, 132, 1)',
                    ],
                    borderColor: [
                        'rgba(75, 192, 192, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(119, 119, 119, 0.8)',
                        'rgba(255,99,132,1)',
                        'rgba(255,99,132,1)',
                        'rgba(255,99,132,1)',
                        'rgba(255,99,132,1)',
                        'rgba(255,99,132,1)',
                        'rgba(255,99,132,1)',
                        'rgba(255,99,132,1)',
                    ],
                    borderWidth: 1,
                    data: [65, 59, 80, 81, 56, 55, 40, 22, 45, 68, 34, 67 ,67, 23, 88],
                },
            ],
        };
        var mySummaryBarChart0 = new Chart(ctx, {
            type: 'bar',
            data: data3,
            options: {
                legend: {
                    display: false,
                    generateLabels: [{
                        hidden: true
                    }]
                },
                tooltips: {
                    enabled: true
                },
                scaleShowLabels : false,
                scales: {
                    xAxes: [{
                        display:false
                    }],
                    yAxes: [{
                        stacked: true
                    }]
                }
            }
        });
//            var myDoughnutChart0 = new Chart(ctx, {
//                type: 'doughnut',
//                data: {
//                    labels: [ "Improve", "Neutral", "Degrade"],
//                    datasets: [
//                        {
//                            label: "qor distribution",
//                            backgroundColor: [
//                                'rgba(153, 204, 51, 1)',
//                                'rgba(119, 119, 119, 0.2)',
//                                'rgba(255, 99, 132, 1)'
//                            ],
//                            borderColor: [
//                                'rgba(75, 192, 192, 1)',
//                                'rgba(119, 119, 119, 0.8)',
//                                'rgba(255,99,132,1)'
//                            ],
//                            borderWidth: 1,
//                            data: [65, 59, 80]
//                        },
//                    ],
//                },
//                  options: {
//                      legend: {
//                          labels: {
//                              boxWidth: 15,
//                          }
//                      },
//                  },
////            });
        mySummaryBarChart0.config.data.datasets[0].data = summary_data[index];
        mySummaryBarChart0.update();
    });

    $("#sqb-switch").text("SUMMARY");
    $(".sqb-summary").css("display","block");
}

function switchStepName(e){
    var listname = $(e).attr('id');
    $("#sqbstep-name-switch").html(listname);
    $("#sqb1-step-name").val(listname);
}

function switchBaseName(e,index1){
    var listname = $(e).attr('id');
    mark = $("#sqc-base-name").val();
    debugger;
    if(listname!=mark){
        $("#sqccmp-name-switch-li").empty();
        $.each(window.steps_list_dict, function(name_list, step) {
            if(name_list == $("#cpattern").text().trim()){
                $.each(step,function(num,dict){
                    if(num>=index1){
                        var li = "<li><a href='#' id='"+dict+"'onclick='switchCmpName(this,"+num+");'>"+dict+"</a></li>"
                        $("#sqccmp-name-switch-li").append(li);
                    }
                })
            }
            mark = listname;
        })
    }
    $("#sqcstep-name-switch").html(listname);
    $("#sqc-base-name").val(listname);
}

function switchCmpName(e,index2){
    var listname = $(e).attr('id');
    debugger;
    mark = $("#sqc-base-name").val();
    debugger;
    if(listname!=mark){
        $("#sqcstep-name-switch-li").empty();
        $.each(window.steps_list_dict, function(name_list, step) {
            if(name_list == $("#cpattern").text().trim()){
                $.each(step,function(num,dict){
                    if(num<=index2){
                        var li = "<li><a href='#' id='"+dict+"'onclick='switchBaseName(this,"+num+");'>"+dict+"</a></li>"
                        $("#sqcstep-name-switch-li").append(li);
                    }
                })
            }
            mark = listname;
        })
    }
    $("#sqccmp-name-switch").html(listname);
    $("#sqc-comp-name").val(listname);
}

function switchSqcMetrics(e) {
    var metrics = $(e).attr('id');
    console.log(metrics);
    $("#sqc-switch").text(metrics);
    $(".sqc-summary").css("display","none");
    $(".sqc-chart").css("display","block");
    window.bs_data = [];
    $.each(window.step_qor_info[metrics], function(design_name, value) {
        if (value == "null") {
            return true;
        }
        $.each(value, function(index, qor_data_list) {
            //console.log(qor_data_list[0])
            var dir = encodeURIComponent($("#sqc-flow-dir").val());
            var pattern = $("#cpattern").text().trim();
            var stage = $("#cstage").text().trim().toLowerCase().substring(2, 6);
            var reg = /\d+/;
            var prevp = qor_data_list[0].match(reg);
            var crntp = qor_data_list[2].match(reg);
            var mt = "http://"+window.location.host+"/profile_"+ stage + "?mode=flow&compress=1&input_list=" + dir +"&cmd=" + stage +"&active_design=" + design_name
                +"&active_metrics=undefined&active_pattern=" + pattern + "&prev_d=0&prev_p=" + prevp + "&crnt_d=0&crnt_p="+ crntp ;
            var data_ele = {
                "design_name": design_name,
                "step_name": qor_data_list[2],
                "step_val": qor_data_list[3],
                "base_name": qor_data_list[0],
                "base_val": qor_data_list[1],
                "pct": qor_data_list[4],
                "link": "<a href='"+ mt +"'>View</a>"
            }
            window.bs_data.push(data_ele)
            //$("#sqb_bs_table").append(trHTML)
        })
        //console.log(design_name)
        //console.log(value)
    });

    var distri_list = getDistriCount(window.bs_data);
    console.log(distri_list);

    myBarChart2.config.data.datasets[0].data = distri_list;
    myBarChart2.update();
    $('#sqc_bs_table').bootstrapTable('destroy').bootstrapTable({
        //toolbar: '#toolbar',                //工具按钮用哪个容器
        striped: true,                      //是否显示行间隔色
        //cache: false,                       //是否使用缓存，默认为true，所以一般情况下需要设置一下这个属性（*）
        pagination: true,                   //是否显示分页（*）
        sortable: true,                     //是否启用排序
        //sortOrder: "asc",                   //排序方式
        //queryParams: oTableInit.queryParams,//传递参数（*）
        //sidePagination: "server",           //分页方式：client客户端分页，server服务端分页（*）
        pageNumber:1,                       //初始化加载第一页，默认第一页
        pageSize: 50,                       //每页的记录行数（*）
        pageList: [10, 25, 50, 100],        //可供选择的每页的行数（*）
        search: true,
        showColumns: true,
        showExport: true,
        //strictSearch: true,
        //clickToSelect: true,                //是否启用点击选中行
        //height: 460,                        //行高，如果没有设置height属性，表格自动根据记录条数觉得表格高度
        //uniqueId: "id",                     //每一行的唯一标识，一般为主键列
        //cardView: false,                    //是否显示详细视图
        //detailView: false,                   //是否显示父子表
        columns: [{
            field: 'design_name',
            title: 'Design Name',
            sortable: true
        }, {
            field: 'step_name',
            title: 'Compare Name',
            sortable: true
        }, {
            field: 'step_val',
            title: 'Step Value',
            sortable: true
        }, {
            field: 'base_name',
            title: 'Base Step',
            sortable: true
        }, {
            field: 'base_val',
            title: 'Base Value',
            sortable: true
        }, {
            field: 'pct',
            title: 'Percentage (%)',
            sortable: true
        },{
            field: 'link',
            title: 'Profile link',
            sortable: true,
        }
        ],
        data: window.bs_data
    });
}

function switchSqcNewMetrics(e){
    $(".sqc-chart").css("display","none");
    var summary1 = [];
    for(key in  window.step_qor_info) {
        summary1.push([key]);
    }
//                console.log(summary);
    summary1_data = [];
    $.each(summary1,function(index,dvalue){
        window.bs_data = [];
        $.each(window.step_qor_info[dvalue], function(design_name, value) {
            if (value == "null") {
                return true;
            }
            $.each(value, function(index, qor_data_list) {
                var data_ele = {
                    "pct": qor_data_list[4]
                };
                window.bs_data.push(data_ele);
            })
        });
        var distri_list = getDistriCount(window.bs_data);
        //console.log(distri_list);
        summary1_data.push(distri_list);
    });

    $(".sqc-summary").empty();
    $.each(summary1,function(index,svalue){
        var newdiv = "<div class='col-md-2'> <div class='panel' style='border-color: #54c7ce;'>"
            +" <div class='panel-heading'>"+svalue+"</div> <canvas id='Sqccanvas"+index+"' width='300' height='300'></canvas></div> </div>";
        $(".sqc-summary").append(newdiv);
        var ctx3 = $("#Sqccanvas"+index).get(0).getContext("2d");
        var data4 = {
            labels: ["-100%+", "-100%", "(-100%~-80%]", "(-80%+~-50%]","(-50%~-20%]", "(-20%~-10%]", "(-10%~-0%)", "0%", "(+0%~+10%)", "[+10%~+20%)", "[+20%~+50%)", "[+50%~+80%)", "[+80%~+100%)", "+100%", "+100%+"],
            datasets: [
                {
                    label: "qor distribution",
                    backgroundColor: [
                        'rgba(153, 204, 51, 1)',
                        'rgba(153, 204, 51, 0.9)',
                        'rgba(153, 204, 51, 0.8)',
                        'rgba(153, 204, 51, 0.6)',
                        'rgba(153, 204, 51, 0.5)',
                        'rgba(153, 204, 51, 0.3)',
                        'rgba(153, 204, 51, 0.1)',
                        'rgba(119, 119, 119, 0.2)',
                        'rgba(255, 99, 132, 0.1)',
                        'rgba(255, 99, 132, 0.3)',
                        'rgba(255, 99, 132, 0.5)',
                        'rgba(255, 99, 132, 0.6)',
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(255, 99, 132, 0.9)',
                        'rgba(255, 99, 132, 1)',

                    ],
                    borderColor: [
                        'rgba(75, 192, 192, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(119, 119, 119, 0.8)',
                        'rgba(255,99,132,1)',
                        'rgba(255,99,132,1)',
                        'rgba(255,99,132,1)',
                        'rgba(255,99,132,1)',
                        'rgba(255,99,132,1)',
                        'rgba(255,99,132,1)',
                        'rgba(255,99,132,1)',
                    ],
                    borderWidth: 1,
                    data: [65, 59, 80, 81, 56, 55, 40, 22, 45, 68, 34, 67 ,67, 23, 88],
                },
            ],
        };
        var mySummaryBarChart1 = new Chart(ctx3, {
            type: 'bar',
            data: data4,
            options: {
                legend: {
                    display: false,
                    generateLabels: [{
                        hidden: true,
                    }]
                },
                tooltips: {
                    enabled: true,
                },
                scaleShowLabels : false,
                scales: {
                    xAxes: [{
                        display:false
                    }],
                    yAxes: [{
                        stacked: true
                    }]
                }
            }
        });
        mySummaryBarChart1.config.data.datasets[0].data = summary1_data[index];
        mySummaryBarChart1.update();
    });

    $("#sqc-switch").text("SUMMARY");
    $(".sqc-summary").css("display","block");
}

function switchSqtMetrics(e) {
    var metrics = $(e).attr('id');
    debugger;
    console.log(metrics);
    $("#sqt-switch").text(metrics);
    $(".sqt-summary").css("display","none");
    $(".sqt-chart").css("display","block");
    window.bs_data = [];
    $.each(window.step_qor_info[metrics], function(design_name, value) {
        if (value == "null") {
            return true;
        }
        $.each(value, function(index, qor_data_list) {
            //console.log(qor_data_list[0])
            var dir = encodeURIComponent($("#sqt1-flow-dir").val());
            var pattern = $("#tpattern").text().trim();
            var stage = $("#tstage").text().trim().toLowerCase().substring(2, 6);
            var reg = /\d+/;
            var prevp = qor_data_list[0].match(reg);
            var crntp = qor_data_list[2].match(reg);
            var mt = "http://"+window.location.host+"/profile_"+ stage + "?mode=flow&compress=1&input_list=" + dir +"&cmd=" + stage +"&active_design=" + design_name
                +"&active_metrics=undefined&active_pattern=" + pattern + "&prev_d=0&prev_p=" + prevp + "&crnt_d=0&crnt_p="+ crntp ;
            var data_ele = {
                "design_name": design_name,
                "step_name": qor_data_list[2],
                "step_val": qor_data_list[3],
                "base_name": qor_data_list[0],
                "base_val": qor_data_list[1],
                "pct": qor_data_list[4],
                "link": "<a href='"+ mt +"'>View</a>"
            }
            window.bs_data.push(data_ele)
            //$("#sqb_bs_table").append(trHTML)
        })
        //console.log(design_name)
        //console.log(value)
    });

    var distri_list = getDistriCount(window.bs_data);
    console.log(distri_list);

    myBarChart3.config.data.datasets[0].data = distri_list;
    myBarChart3.update();
    $('#sqt_bs_table').bootstrapTable('destroy').bootstrapTable({
        //toolbar: '#toolbar',                //工具按钮用哪个容器
        striped: true,                      //是否显示行间隔色
        //cache: false,                       //是否使用缓存，默认为true，所以一般情况下需要设置一下这个属性（*）
        pagination: true,                   //是否显示分页（*）
        sortable: true,                     //是否启用排序
        //sortOrder: "asc",                   //排序方式
        //queryParams: oTableInit.queryParams,//传递参数（*）
        //sidePagination: "server",           //分页方式：client客户端分页，server服务端分页（*）
        pageNumber:1,                       //初始化加载第一页，默认第一页
        pageSize: 50,                       //每页的记录行数（*）
        pageList: [10, 25, 50, 100],        //可供选择的每页的行数（*）
        search: true,
        showColumns: true,
        showExport: true,
        //strictSearch: true,
        //clickToSelect: true,                //是否启用点击选中行
        //height: 460,                        //行高，如果没有设置height属性，表格自动根据记录条数觉得表格高度
        //uniqueId: "id",                     //每一行的唯一标识，一般为主键列
        //cardView: false,                    //是否显示详细视图
        //detailView: false,                   //是否显示父子表
        columns: [{
            field: 'design_name',
            title: 'Design Name',
            sortable: true
        }, {
            field: 'step_name',
            title: 'Step Name',
            sortable: true
        }, {
            field: 'step_val',
            title: 'Step Value',
            sortable: true
        }, {
            field: 'base_name',
            title: 'Base Step',
            sortable: true
        }, {
            field: 'base_val',
            title: 'Base Value',
            sortable: true
        }, {
            field: 'pct',
            title: 'Percentage (%)',
            sortable: true
        },{
            field: 'link',
            title: 'Profile link',
            sortable: true,

        }
        ],
        data: window.bs_data
    });
}

function switchSqtNewMetrics(e){
    $(".sqt-chart").css("display","none");
    var summary = [];
    for(key in  window.step_qor_info) {
        summary.push([key]);
    }
    summary_data = [];
    $.each(summary,function(index,dvalue){
        window.bs_data = [];
        $.each(window.step_qor_info[dvalue], function(design_name, value) {
            if (value == "null") {
                return true;
            }
            $.each(value, function(index, qor_data_list) {
                var data_ele = {
                    "pct": qor_data_list[4]
                };
                window.bs_data.push(data_ele);
            })
        });
        var distri_list = getDistriCount(window.bs_data);
        //console.log(distri_list);
        summary_data.push(distri_list);
    });

    $(".sqt-summary").empty();
    $.each(summary,function(index,svalue){
        var newdiv = "<div class='col-md-2'> <div class='panel' style='border-color: #54c7ce;'>"
            +" <div class='panel-heading'>"+svalue+"</div> <canvas id='canvas"+index+"' width='300' height='300'></canvas></div> </div>";
        $(".sqt-summary").append(newdiv);
        var ctx = $("#canvas"+index).get(0).getContext("2d");
        var data3 = {
            labels: ["-100%+", "-100%", "(-100%~-80%]", "(-80%+~-50%]","(-50%~-20%]", "(-20%~-10%]", "(-10%~-0%)", "0%", "(+0%~+10%)", "[+10%~+20%)", "[+20%~+50%)", "[+50%~+80%)", "[+80%~+100%)", "+100%", "+100%+"],
            datasets: [
                {
                    label: "qor distribution",
                    backgroundColor: [
                        'rgba(153, 204, 51, 1)',
                        'rgba(153, 204, 51, 0.9)',
                        'rgba(153, 204, 51, 0.8)',
                        'rgba(153, 204, 51, 0.6)',
                        'rgba(153, 204, 51, 0.5)',
                        'rgba(153, 204, 51, 0.3)',
                        'rgba(153, 204, 51, 0.1)',
                        'rgba(119, 119, 119, 0.2)',
                        'rgba(255, 99, 132, 0.1)',
                        'rgba(255, 99, 132, 0.3)',
                        'rgba(255, 99, 132, 0.5)',
                        'rgba(255, 99, 132, 0.6)',
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(255, 99, 132, 0.9)',
                        'rgba(255, 99, 132, 1)',
                    ],
                    borderColor: [
                        'rgba(75, 192, 192, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(119, 119, 119, 0.8)',
                        'rgba(255,99,132,1)',
                        'rgba(255,99,132,1)',
                        'rgba(255,99,132,1)',
                        'rgba(255,99,132,1)',
                        'rgba(255,99,132,1)',
                        'rgba(255,99,132,1)',
                        'rgba(255,99,132,1)',
                    ],
                    borderWidth: 1,
                    data: [65, 59, 80, 81, 56, 55, 40, 22, 45, 68, 34, 67 ,67, 23, 88],
                },
            ],
        };
        var mySummaryBarChart0 = new Chart(ctx, {
            type: 'bar',
            data: data3,
            options: {
                legend: {
                    display: false,
                    generateLabels: [{
                        hidden: true
                    }]
                },
                tooltips: {
                    enabled: true
                },
                scaleShowLabels : false,
                scales: {
                    xAxes: [{
                        display:false
                    }],
                    yAxes: [{
                        stacked: true
                    }]
                }
            }
        });

        mySummaryBarChart0.config.data.datasets[0].data = summary_data[index];
        mySummaryBarChart0.update();
    });

    $("#sqt-switch").text("SUMMARY");
    $(".sqt-summary").css("display","block");
}

function getDistriCount(obj) {
    var distri_list = [];
    var filter_list = filterDistriCount(obj);
    $.each(filter_list,function(index,value){
        distri_list.push(value.length);
    })
    return distri_list
}

function filterDistriCount(obj) {
    var distri_list = []
    var filtered_obj = $.grep(obj, function(v) {
        return parseFloat(v.pct) < -100;
    });
    distri_list.push(filtered_obj)

    var filtered_obj = $.grep(obj, function(v) {
        return parseFloat(v.pct) == -100;
    });
    distri_list.push(filtered_obj)

    var filtered_obj = $.grep(obj, function(v) {
        return parseFloat(v.pct) > -100 && parseFloat(v.pct) <= -80;
    });
    distri_list.push(filtered_obj)

    var filtered_obj = $.grep(obj, function(v) {
        return parseFloat(v.pct) > -80 && parseFloat(v.pct) <= -50;
    });
    distri_list.push(filtered_obj)

    var filtered_obj = $.grep(obj, function(v) {
        return parseFloat(v.pct) > -50 && parseFloat(v.pct) <= -20;
    });
    distri_list.push(filtered_obj)

    var filtered_obj = $.grep(obj, function(v) {
        return parseFloat(v.pct) > -20 && parseFloat(v.pct) <= -10;
    });
    distri_list.push(filtered_obj)

    var filtered_obj = $.grep(obj, function(v) {
        return parseFloat(v.pct) > -10 && parseFloat(v.pct) < 0;
    });
    distri_list.push(filtered_obj)

    var filtered_obj = $.grep(obj, function(v) {
        return parseFloat(v.pct) == 0;
    });
    distri_list.push(filtered_obj)

    var filtered_obj = $.grep(obj, function(v) {
        return parseFloat(v.pct) > 0 && parseFloat(v.pct) < 10;
    });
    distri_list.push(filtered_obj)

    var filtered_obj = $.grep(obj, function(v) {
        return parseFloat(v.pct) >= 10 && parseFloat(v.pct) < 20;
    });
    distri_list.push(filtered_obj)

    var filtered_obj = $.grep(obj, function(v) {
        return parseFloat(v.pct) >= 20 && parseFloat(v.pct) < 50;
    });
    distri_list.push(filtered_obj)

    var filtered_obj = $.grep(obj, function(v) {
        return parseFloat(v.pct) >= 50 && parseFloat(v.pct) < 80;
    });
    distri_list.push(filtered_obj)

    var filtered_obj = $.grep(obj, function(v) {
        return parseFloat(v.pct) >= 80 && parseFloat(v.pct) < 100;
    });
    distri_list.push(filtered_obj)

    var filtered_obj = $.grep(obj, function(v) {
        return parseFloat(v.pct) == 100;
    });
    distri_list.push(filtered_obj)

    var filtered_obj = $.grep(obj, function(v) {
        return parseFloat(v.pct) > 100;
    });
    distri_list.push(filtered_obj)

    return distri_list
}

function getNewDistriCount(obj) {
    var distri_list = []

    var filtered_obj = $.grep(obj, function(v) {
        return parseFloat(v.pct) < 0;
    });
    distri_list.push(filtered_obj.length)

    var filtered_obj = $.grep(obj, function(v) {
        return parseFloat(v.pct) == 0;
    });
    distri_list.push(filtered_obj.length)

    var filtered_obj = $.grep(obj, function(v) {
        return parseFloat(v.pct) > 0
    });
    distri_list.push(filtered_obj.length)
    return distri_list
}

function activeSQBMethod(e) {
    var method = $(e).attr('id');
    var method_full = $(e).text();
    //console.log(mode);
    $("#method").text(method_full);
    $(".sqc-chart").css("display","none");
    $(".sqc-switch").css("display","none");
    $(".sqb-summary").css("display","none");
    $(".sqc-summary").css("display","none");
    $("#error-warning").css("display","none");
    $(".analysis_area").css("display", "none");
    $("#sqb-hide").css("display","none");
    $(".sqt-chart").css("display","none");
    $(".sqt-switch").css("display","none");
    $(".sqt-summary").css("display","none");
    // $("#sqb1-step-name").css("display","none");
    // $("#pattern").css("display","none");
    $("."+method).css("display", "table");
    //console.log($("#compress-mode").val());
}

function activeSQCMethod(e) {
    var method = $(e).attr('id');
    var method_full = $(e).text();
    //console.log(mode);
    $("#method").text(method_full);
    $(".sqb-chart").css("display","none");
    $(".sqc-switch").css("display","none");
    $(".sqc-chart").css("display","none");
    $(".sqb-switch").css("display","none");
    $(".sqb-summary").css("display","none");
    $(".sqc-summary").css("display","none");
    $("#sqc-hide").css("display","none");
    $(".sqt-chart").css("display","none");
    $(".sqt-switch").css("display","none");
    $(".sqt-summary").css("display","none");
    // $("#sqc-base-name").css("display","none");
    // $("#sqc-comp-name").css("display","none");
    // $("#cpattern").css("display","none");
    $("#error-warning").css("display","none");
    $(".analysis_area").css("display", "none");
    $("."+method).css("display", "table");
    //console.log($("#compress-mode").val());
}

function activeSQAMethod(e){
    var method = $(e).attr('id');
    var method_full = $(e).text();
    //console.log(mode);
    $("#method").text(method_full);
    $(".sqb-chart").css("display","none");
    $(".sqc-switch").css("display","none");
    $(".sqc-chart").css("display","none");
    $(".sqb-switch").css("display","none");
    $(".sqb-summary").css("display","none");
    $(".sqc-summary").css("display","none");
    $("#sqt-hide").css("display","none");
    $(".sqt-chart").css("display","none");
    $(".sqt-switch").css("display","none");
    $(".sqt-summary").css("display","none");
    // $("#sqc-base-name").css("display","none");
    // $("#sqc-comp-name").css("display","none");
    // $("#cpattern").css("display","none");
    $("#error-warning").css("display","none");
    $(".analysis_area").css("display", "none");
    $("."+method).css("display", "table");
    //console.log($("#compress-mode").val());
}

function activeMode(e) {
    var mode = $(e).text();
    //console.log(mode);
    $("#mode").html(mode+" <span class=\"caret\"></span>");
    //console.log($("#compress-mode").val());
}

function activeStage(e) {
    var stage = $(e).text();
    //console.log(mode)
    $("#stage").html(stage+" <span class=\"caret\"></span>");
    //console.log($("#compress-mode").val());
}

function activePattern(e) {
    var pattern = $(e).text();
    //console.log(mode);
    $("#pattern").html(pattern+" <span class=\"caret\"></span>");
    var stepname = window.steps_list_dict[$("#pattern").text().trim()][0];
    $("#sqbstep-name-switch").html(stepname);
    $("#sqb1-step-name").val(stepname);
    $("#sqbstep-name-switch-li").empty();
    $.each(window.steps_list_dict, function(name_list, step) {
        if(name_list == $("#pattern").text().trim()){
            $.each(step,function(dict){
                var li = "<li><a href='#' id='"+step[dict]+"'onclick='switchStepName(this);'>"+step[dict]+"</a></li>"
                $("#sqbstep-name-switch-li").append(li);
            })
        }
    })
    //console.log($("#compress-mode").val());
}

function activeSqcStage(e) {
    var stage = $(e).text();
    //console.log(mode);
    $("#cstage").html(stage+" <span class=\"caret\"></span>");
    //console.log($("#compress-mode").val());
}

function activeSqcPattern(e) {
    var pattern = $(e).text();
    $("#cpattern").html(pattern+" <span class=\"caret\"></span>");
    var stepname = window.steps_list_dict[$("#cpattern").text().trim()][0];
    $("#sqcstep-name-switch").html(stepname);
    $("#sqc-base-name").val(stepname);
    $("#sqcstep-name-switch-li").empty();
    $("#sqccmp-name-switch-li").empty();
    $.each(window.steps_list_dict, function(name_list, step) {
        debugger;
        if(name_list == $("#cpattern").text().trim()){
            $.each(step,function(index1,dict){
                var li = "<li><a href='#' id='"+dict+"'onclick='switchBaseName(this,"+index1+");'>"+dict+"</a></li>"
                $("#sqcstep-name-switch-li").append(li);
            })
            $.each(step,function(index2,dict){
                if(index2>0){
                    var li = "<li><a href='#' id='"+dict+"'onclick='switchCmpName(this,"+index2+");'>"+dict+"</a></li>"
                    $("#sqccmp-name-switch-li").append(li);
                }
            })
        }
    })
}

function activeSqtStage(e) {
    var stage = $(e).text();
    //console.log(mode)
    $("#tstage").html(stage+" <span class=\"caret\"></span>");
    //console.log($("#compress-mode").val());
}

function activeSqtPattern(e) {
    var pattern = $(e).text();
    //console.log(mode);
    $("#tpattern").html(pattern+" <span class=\"caret\"></span>");
    var stepname = window.steps_list_dict[$("#tpattern").text().trim()][0];
    $("#sqtstep-name-switch").html(stepname);
    $("#sqt1-step-name").val(stepname);
    $("#sqtstep-name-switch-li").empty();
    $.each(window.steps_list_dict, function(name_list, step) {
        if(name_list == $("#tpattern").text().trim()){
            $.each(step,function(dict){
                var li = "<li><a href='#' id='"+step[dict]+"'onclick='switchStepName(this);'>"+step[dict]+"</a></li>"
                $("#sqtstep-name-switch-li").append(li);
            })
        }
    })
    //console.log($("#compress-mode").val());
}
function isEmptyObject(e) {
    var t;
    for (t in e)
        return !1;
    return !0;
}

$(function() {

    //$(".gain-loss-display").css("display","none");
    $('#sqb_btn').click(function(e){
        $("#sqb-hide").css("display","none");
        $(".sqb-chart").css("display","none");
        $(".sqb-switch").css("display","none");
        $(".sqc-chart").css("display","none");
        $(".sqc-switch").css("display","none");
        $(".sqc-summary").css("display","none");
        $(".sqb-summary").css("display","none");

        $("#error-warning").css("display","none");
        var warn = $("#error-warning");
        warn.text("");
        $("#pattern").html("Pattern"+" <span class=\"caret\"></span>");
        $("#sqbstep-name-switch").text("Step name");
        if( $("#sqb1-flow-dir").val()==""){
            warn.css("display","block");
            warn.attr("class","alert alert-warning");
            warn.append("<strong>flow_dir</strong> should not be empty!");
            return false;
        }
        if($("#stage").text().trim()=="Stage"){
            warn.css("display","block");
            warn.attr("class","alert alert-warning");
            warn.append("<strong>Stage</strong> Warn! Please choose the right stage! ");
            return false;
        }
        var l = Ladda.create(this);
        l.start();
        $.post('analysis_sqb', {
            step_name: "",
            flow_dir: $("#sqb1-flow-dir").val(),
            pattern: $("#pattern").text().trim(),
            stage: $("#stage").text().trim()
        }, function () {
            console.log("sending post...")
        })
            .done(function(data) {
                // window.steps_list_dict = ["NWPOPT","NWCOPT","NWFOPT"];
                if(data["result"]=="success"){
                    judgeEmpty = jQuery.parseJSON(data["steps_list_dict"]);
                    if(isEmptyObject(judgeEmpty)){
                        warn.css("display","block");
                        warn.attr("class","alert alert-warning");
                        warn.append("<strong>Data</strong> do not exist");
                        l.stop();
                        return false;
                    }
                }
                else{
                    warn.css("display","block");
                    warn.attr("class","alert alert-danger");
                    warn.append(data["msg"]);
                    l.stop();
                    return false;
                }
                window.steps_list_dict = jQuery.parseJSON(data["steps_list_dict"]);
                console.log(steps_list_dict);
                $("#sqb-hide").css("display","block");
                $("#pattern-switch-li").empty();
                $.each(window.steps_list_dict, function(name_list, pattern) {
                    var li = "<li><a href='#' id='"+name_list+"'onclick='activePattern(this);'>"+name_list+"</a></li>"
                    $("#pattern-switch-li").append(li);
                })
                console.log("first start success!");
                l.stop();
            })
            .fail(function() {
                //$(destId).text("Error: Could not contact server.");
                l.stop();
                console.log("fail!")
            });

    })
    $('#sqb_btn1').click(function(e) {
        //console.log($("#sqb1-step-name").val())
        $(".sqb-chart").css("display","none");
        $(".sqb-switch").css("display","none");
        $(".sqc-chart").css("display","none");
        $(".sqc-switch").css("display","none");
        $("#error-warning").css("display","none");

        var warn = $("#error-warning");
        warn.text("");
        if($("#pattern").text().trim()=="Pattern"){
            warn.css("display","block");
            warn.attr("class","alert alert-warning");
            warn.append("<strong>Pattern</strong> Warn! Please choose the right pattern! ");
            return false;
        }
        if($("#sqb1-step-name").val()==""){
            warn.css("display","block");
            warn.attr("class","alert alert-warning");
            warn.append("<strong>Step name</strong> should not be empty!");
            return false;
        }
        var l = Ladda.create(this);
        l.start();
        $.post('analysis_sqb', {
            step_name: $("#sqb1-step-name").val(),
            flow_dir: $("#sqb1-flow-dir").val(),
            pattern: $("#pattern").text().trim(),
            stage: $("#stage").text().trim()
        }, function () {
            console.log("sending post...")
        })
            .done(function(data) {
                //var thHTML='<thead><tr><th data-sortable="true" data-field="design_name"> design_name </th>
                // <th data-sortable="true" data-field="step_name"> step_name </th><th data-sortable="true" data-field="step_val">
                // step_val</th><th data-sortable="true" data-field="base_step"> base_step </th><th data-sortable="true" data-field="base_val">
                // base_val</th><th data-sortable="true" data-field="Gain-Loss"> Gain/Loss Pct.</th></tr></thead>'
                //$("#sqb_bs_table").append(thHTML)\
                debugger;
                // window.steps_list_dict = ["NWPOPT","NWCOPT","NWFOPT"];
                window.bs_data = [];
                if(data["result"]=="success"){
                    judgeEmpty = jQuery.parseJSON(data["step_qor_info"]);
                    if(isEmptyObject(judgeEmpty)){
                        warn.css("display","block");
                        warn.attr("class","alert alert-warning");
                        warn.append("<strong>Data</strong> do not exist");
                        l.stop();
                        return false;
                    }
                }
                else{
                    warn.css("display","block");
                    warn.attr("class","alert alert-danger");
                    warn.append(data["msg"]);
                    l.stop();
                    return false;
                }

                window.step_qor_info = jQuery.parseJSON(data["step_qor_info"]);
                metrics = data['default_metrics'];
                console.log(window.step_qor_info);
                $.each(window.step_qor_info[metrics], function(design_name, value) {
                    if (value == "null") {
                        return true;
                    }
                    $.each(value, function(index, qor_data_list) {
                        //console.log(qor_data_list[0])
                        var dir = encodeURIComponent($("#sqb1-flow-dir").val());
                        var pattern = $("#pattern").text().trim();
                        var stage = $("#stage").text().trim().toLowerCase().substring(2, 6);
                        var reg = /\d+/;
                        var prevp = qor_data_list[0].match(reg);
                        var crntp = qor_data_list[2].match(reg);
                        var mt = "http://"+window.location.host+"/profile_"+ stage + "?mode=flow&compress=1&input_list=" + dir +"&cmd=" + stage +"&active_design=" + design_name+"&active_metrics=undefined&active_pattern=" + pattern + "&prev_d=0&prev_p=" + prevp + "&crnt_d=0&crnt_p="+ crntp ;
                        var data_ele = {
                            "design_name": design_name,
                            "step_name": qor_data_list[2],
                            "step_val": qor_data_list[3],
                            "base_name": qor_data_list[0],
                            "base_val": qor_data_list[1],
                            "pct": qor_data_list[4],
                            "link": "<a href='"+ mt +"'>View</a>"
                        }
                        window.bs_data.push(data_ele)
                        //$("#sqb_bs_table").append(trHTML)
                    })
                    //console.log(design_name)
                    //console.log(value)
                })
                $("#sqb-switch").text(metrics);
                $("#sqb-switch-li").empty();
                $.each(window.step_qor_info, function(metrics, dict) {
                    var li = "<li><a href='#' id='"+metrics+"' onclick='switchMetrics(this);'>"+metrics+"</a></li>"
                    $("#sqb-switch-li").append(li);
                })
                var li = "<li><a href='#' id='summary' onclick='switchNewMetrics(this);'>"+"SUMMARY"+"</a></li>"
                $("#sqb-switch-li").append(li);
                var distri_list = getDistriCount(window.bs_data);
//                      console.log(distri_list)

                myBarChart.config.data.datasets[0].data = distri_list;
                myBarChart.update();

                $('#sqb_bs_table').bootstrapTable('destroy').bootstrapTable({
                    //toolbar: '#toolbar',                //工具按钮用哪个容器
                    striped: true,                      //是否显示行间隔色
                    //cache: false,                       //是否使用缓存，默认为true，所以一般情况下需要设置一下这个属性（*）
                    pagination: true,                   //是否显示分页（*）
                    sortable: true,                     //是否启用排序
                    //sortOrder: "asc",                   //排序方式
                    //queryParams: oTableInit.queryParams,//传递参数（*）
                    //sidePagination: "server",           //分页方式：client客户端分页，server服务端分页（*）
                    pageNumber:1,                       //初始化加载第一页，默认第一页
                    pageSize: 50,                       //每页的记录行数（*）
                    pageList: [10, 25, 50, 100],        //可供选择的每页的行数（*）
                    search: true,
                    showExport: true,                    //是否显示导出
                    exportDataType: "all",
                    showColumns: true,
//                            showPaginationSwitch:true,
                    //strictSearch: true,
                    //clickToSelect: true,                //是否启用点击选中行
                    //height: 460,                        //行高，如果没有设置height属性，表格自动根据记录条数觉得表格高度
                    //uniqueId: "id",                     //每一行的唯一标识，一般为主键列
                    //cardView: false,                    //是否显示详细视图
                    //detailView: false,                   //是否显示父子表
                    columns: [{
                        field: 'design_name',
                        title: 'Design Name',
                        sortable: true
                    }, {
                        field: 'step_name',
                        title: 'Step Name',
                        sortable: true
                    }, {
                        field: 'step_val',
                        title: 'Step Value',
                        sortable: true
                    }, {
                        field: 'base_name',
                        title: 'Base Step',
                        sortable: true
                    }, {
                        field: 'base_val',
                        title: 'Base Value',
                        sortable: true
                    }, {
                        field: 'pct',
                        title: 'Percentage (%)',
                        sortable: true
                    },{
                        field: 'link',
                        title: 'Profile link',
                        sortable: true,
                    }
                    ],
                    data: window.bs_data
                });

                //$('#sqb_bs_table')
                // $("#sqb1-step-name").css("display","block");
                // $("#stage").css("display","block");
                $("#sqb-hide").css("display","block");
                $(".sqb-chart").css("display","block");
                $(".sqb-switch").css("display", "table");
                console.log("success!");
                l.stop();
            })
            .fail(function() {
                //$(destId).text("Error: Could not contact server.");
                l.stop();
                console.log("fail!")
            });
    })

    $('#sqc_btn').click(function(e){
        $(".sqc-summary").css("display","none");
        $(".sqb-summary").css("display","none");
        $("#sqc-hide").css("display","none");
        $(".sqb-chart").css("display","none");
        $(".sqb-switch").css("display","none");
        $(".sqc-chart").css("display","none");
        $(".sqc-switch").css("display","none");
        $("#error-warning").css("display","none");
        var warn = $("#error-warning");
        warn.text("");
        $("#sqccmp-name-switch-li").empty();
        $("#sqcbase-name-switch-li").empty();
        $("#cpattern").html("Pattern"+" <span class=\"caret\"></span>");
        $("#sqcstep-name-switch").text("Base");
        if( $("#sqc-flow-dir").val()==""){
            warn.css("display","block");
            warn.attr("class","alert alert-warning");
            warn.append("<strong>flow_dir</strong> should not be empty!");
            return false;
        }
        if($("#cstage").text().trim()=="Stage"){
            warn.css("display","block");
            warn.attr("class","alert alert-warning");
            warn.append("<strong>Stage</strong> Warn! Please choose the right stage! ");
            return false;
        }
        var l = Ladda.create(this);
        l.start();
        $.post('analysis_sqc', {
            step_name: "",
            base_name: "",
            flow_dir: $("#sqc-flow-dir").val(),
            pattern: $("#cpattern").text().trim(),
            stage: $("#cstage").text().trim()
        }, function () {
            console.log("sending post...")
        })
            .done(function(data) {
                // window.steps_list_dict = ["NWPOPT","NWCOPT","NWFOPT"];
                if(data["result"]=="success"){
                    judgeEmpty = jQuery.parseJSON(data["steps_list_dict"]);
                    if(isEmptyObject(judgeEmpty)){
                        warn.css("display","block");
                        warn.attr("class","alert alert-warning");
                        warn.append("<strong>Data</strong> do not exist");
                        l.stop();
                        return false;
                    }
                }
                else{
                    warn.css("display","block");
                    warn.attr("class","alert alert-danger");
                    warn.append(data["msg"]);
                    l.stop();
                    return false;
                }
                window.steps_list_dict = jQuery.parseJSON(data["steps_list_dict"]);
                console.log(steps_list_dict);
                $("#sqc-hide").css("display","block");
                $("#cpattern-switch-li").empty();
                $.each(window.steps_list_dict, function(name_list, pattern) {
                    var li = "<li><a href='#' id='"+name_list+"'onclick='activeSqcPattern(this);'>"+name_list+"</a></li>"
                    $("#cpattern-switch-li").append(li);
                })
                console.log("first start success!");
                l.stop();
            })
            .fail(function() {
                //$(destId).text("Error: Could not contact server.");
                l.stop();
                console.log("fail!")
            });

    })
    $('#sqc_btn1').click(function(e) {
        $(".sqb-chart").css("display","none");
        $(".sqb-switch").css("display","none");
        $(".sqc-chart").css("display","none");
        $(".sqc-switch").css("display","none");
        $("#error-warning").css("display","none");
        var warn = $("#error-warning");
        warn.text("");
        if( $("#sqc-base-name").val()==""){
            warn.css("display","block");
            warn.attr("class","alert alert-warning");
            warn.append("<strong>Base name</strong> should not be empty!");
            return false;
        }
        if( $("#sqc-comp-name").val()==""){
            warn.css("display","block");
            warn.attr("class","alert alert-warning");
            warn.append("<strong>Compare name</strong> should not be empty!");
            return false;
        }
        if($("#cpattern").text().trim()=="Pattern"){
            warn.css("display","block");
            warn.attr("class","alert alert-warning");
            warn.append("<strong>Pattern </strong> Warn! Please choose the right Pattern! ");
            return false;
        }
        var l = Ladda.create(this);
        l.start();
        $.post('analysis_sqc', {
            base_name: $("#sqc-base-name").val(),
            step_name: $("#sqc-comp-name").val(),
            flow_dir: $("#sqc-flow-dir").val(),
            pattern: $("#cpattern").text().trim(),
            stage: $("#cstage").text().trim()
        }, function () {
            console.log("sending analysis compare post...")
        })
            .done(function(data) {
                window.bs_data = [];
                debugger;
                if(data["result"]=="success"){
                    judgeEmpty = jQuery.parseJSON(data["step_qor_info"]);
                    if(isEmptyObject(judgeEmpty)){
                        warn.css("display","block");
                        warn.attr("class","alert alert-warning");
                        warn.append("<strong>Data</strong> do not exist");
                        l.stop();
                        return false;
                    }
                }
                else{
                    warn.css("display","block");
                    warn.attr("class","alert alert-danger");
                    warn.append(data["msg"]);
                    l.stop();
                    return false;
                }
                window.step_qor_info = jQuery.parseJSON(data["step_qor_info"]);
                metrics = data['default_metrics'];
                console.log(window.step_qor_info);
                $.each(window.step_qor_info[metrics], function(design_name, value) {
                    if (value == "null") {
                        return true;
                    }
                    $.each(value, function(index, qor_data_list) {
                        //console.log(qor_data_list[0])
                        var dir = encodeURIComponent($("#sqc-flow-dir").val());
                        var pattern = $("#cpattern").text().trim();
                        var stage = $("#cstage").text().trim().toLowerCase().substring(2, 6);
                        var reg = /\d+/;
                        var prevp = qor_data_list[0].match(reg);
                        var crntp = qor_data_list[2].match(reg);
                        var mt = "http://"+window.location.host+"/profile_"+ stage + "?mode=flow&compress=1&input_list=" + dir +"&cmd=" + stage +"&active_design=" + design_name
                            +"&active_metrics=undefined&active_pattern=" + pattern + "&prev_d=0&prev_p=" + prevp + "&crnt_d=0&crnt_p="+ crntp ;
                        var data_ele = {
                            "design_name": design_name,
                            "step_name": qor_data_list[2],
                            "step_val": qor_data_list[3],
                            "base_name": qor_data_list[0],
                            "base_val": qor_data_list[1],
                            "pct": qor_data_list[4],
                            "link": "<a href='"+ mt +"'>View</a>"
                        }
                        window.bs_data.push(data_ele)
                        //$("#sqb_bs_table").append(trHTML)
                    })
                    //console.log(design_name)
                    //console.log(value)
                })
                $("#sqc-switch").text(metrics);
                $("#sqc-switch-li").empty();
                $.each(window.step_qor_info, function(metrics, dict) {
                    var li = "<li><a href='#' id='"+metrics+"' onclick='switchSqcMetrics(this);'>"+metrics+"</a></li>"
                    $("#sqc-switch-li").append(li);
                })
                var li = "<li><a href='#' id='summary1' onclick='switchSqcNewMetrics(this);'>"+"SUMMARY"+"</a></li>"
                $("#sqc-switch-li").append(li);
                var distri_list = getDistriCount(window.bs_data);
//                      console.log(distri_list)

                myBarChart2.config.data.datasets[0].data = distri_list;
                myBarChart2.update();

                $('#sqc_bs_table').bootstrapTable('destroy').bootstrapTable({
                    //toolbar: '#toolbar',                //工具按钮用哪个容器
                    striped: true,                      //是否显示行间隔色
                    //cache: false,                       //是否使用缓存，默认为true，所以一般情况下需要设置一下这个属性（*）
                    pagination: true,                   //是否显示分页（*）
                    sortable: true,                     //是否启用排序
                    //sortOrder: "asc",                   //排序方式
                    //queryParams: oTableInit.queryParams,//传递参数（*）
                    //sidePagination: "server",           //分页方式：client客户端分页，server服务端分页（*）
                    pageNumber:1,                       //初始化加载第一页，默认第一页
                    pageSize: 50,                       //每页的记录行数（*）
                    pageList: [10, 25, 50, 100],        //可供选择的每页的行数（*）
                    search: true,
                    showExport: true,                    //是否显示导出
                    exportDataType: "all",
                    showColumns: true,
//                            showPaginationSwitch:true,
                    //strictSearch: true,
                    //clickToSelect: true,                //是否启用点击选中行
                    //height: 460,                        //行高，如果没有设置height属性，表格自动根据记录条数觉得表格高度
                    //uniqueId: "id",                     //每一行的唯一标识，一般为主键列
                    //cardView: false,                    //是否显示详细视图
                    //detailView: false,                   //是否显示父子表
                    columns: [{
                        field: 'design_name',
                        title: 'Design Name',
                        sortable: true
                    }, {
                        field: 'step_name',
                        title: 'Compare Name',
                        sortable: true
                    }, {
                        field: 'step_val',
                        title: 'Step Value',
                        sortable: true
                    }, {
                        field: 'base_name',
                        title: 'Base Step',
                        sortable: true
                    }, {
                        field: 'base_val',
                        title: 'Base Value',
                        sortable: true
                    }, {
                        field: 'pct',
                        title: 'Percentage (%)',
                        sortable: true
                    },{
                        field: 'link',
                        title: 'Profile link',
                        sortable: true,
                    }
                    ],
                    data: window.bs_data
                });

                //$('#sqb_bs_table')

                $(".sqc-chart").css("display","block");
                $(".sqc-switch").css("display", "table");
                console.log("compare_analysis success!");
                l.stop();
            })
            .fail(function() {
                //$(destId).text("Error: Could not contact server.");
                l.stop();
                console.log("fail!")
            });
    })

    $('#sqt_btn').click(function(e){
        $("#sqt-hide").css("display","none");
        $(".sqb-chart").css("display","none");
        $(".sqb-switch").css("display","none");
        $(".sqc-chart").css("display","none");
        $(".sqc-switch").css("display","none");
        $(".sqc-summary").css("display","none");
        $(".sqb-summary").css("display","none");
        $(".sqt-chart").css("display","none");
        $(".sqt-switch").css("display","none");
        $(".sqt-summary").css("display","none");

        $("#error-warning").css("display","none");
        var warn = $("#error-warning");
        warn.text("");
        $("#tpattern").html("Pattern"+" <span class=\"caret\"></span>");
        $("#sqtstep-name-switch").text("Step name");
        if( $("#sqt1-flow-dir").val()==""){
            warn.css("display","block");
            warn.attr("class","alert alert-warning");
            warn.append("<strong>flow_dir</strong> should not be empty!");
            return false;
        }
        if($("#tstage").text().trim()=="Stage"){
            warn.css("display","block");
            warn.attr("class","alert alert-warning");
            warn.append("<strong>Stage</strong> Warn! Please choose the right stage! ");
            return false;
        }
        var l = Ladda.create(this);
        l.start();
        $.post('analysis_sqt', {
            step_name: $("#sqc-base-name").val(),
            flow_dir: $("#sqt1-flow-dir").val(),
            pattern: $("#tpattern").text().trim(),
            stage: $("#tstage").text().trim(),
            bound: $("#sqt-bound").val(),
        }, function () {
            console.log("sending post...")
        })
            .done(function(data) {
                // window.steps_list_dict = ["NWPOPT","NWCOPT","NWFOPT"];
                if(data["result"]=="success"){
                    judgeEmpty = jQuery.parseJSON(data["steps_list_dict"]);
                    if(isEmptyObject(judgeEmpty)){
                        warn.css("display","block");
                        warn.attr("class","alert alert-warning");
                        warn.append("<strong>Data</strong> do not exist");
                        l.stop();
                        return false;
                    }
                }
                else{
                    warn.css("display","block");
                    warn.attr("class","alert alert-danger");
                    warn.append(data["msg"]);
                    l.stop();
                    return false;
                }
                window.steps_list_dict = jQuery.parseJSON(data["steps_list_dict"]);
                console.log(steps_list_dict);
                $("#sqt-hide").css("display","block");
                $("#tpattern-switch-li").empty();
                $.each(window.steps_list_dict, function(name_list, pattern) {
                    var li = "<li><a href='#' id='"+name_list+"'onclick='activeSqtPattern(this);'>"+name_list+"</a></li>"
                    $("#tpattern-switch-li").append(li);
                })
                console.log("first start success!");
                l.stop();
            })
            .fail(function() {
                //$(destId).text("Error: Could not contact server.");
                l.stop();
                console.log("fail!")
            });

    })
    $('#sqt_btn1').click(function(e) {
        //console.log($("#sqb1-step-name").val())
        $(".sqb-chart").css("display","none");
        $(".sqb-switch").css("display","none");
        $(".sqc-chart").css("display","none");
        $(".sqc-switch").css("display","none");
        $("#error-warning").css("display","none");

        var warn = $("#error-warning");
        warn.text("");
        if($("#tpattern").text().trim()=="Pattern"){
            warn.css("display","block");
            warn.attr("class","alert alert-warning");
            warn.append("<strong>Pattern</strong> Warn! Please choose the right pattern! ");
            return false;
        }
        if($("#sqt1-step-name").val()==""){
            warn.css("display","block");
            warn.attr("class","alert alert-warning");
            warn.append("<strong>Step name</strong> should not be empty!");
            return false;
        }
        var l = Ladda.create(this);
        l.start();
        $.post('analysis_sqt', {
            step_name: $("#sqt1-step-name").val(),
            flow_dir: $("#sqt1-flow-dir").val(),
            pattern: $("#tpattern").text().trim(),
            stage: $("#tstage").text().trim(),
            bound: $("#sqt-bound").val(),
        }, function () {
            console.log("sending post...")
        })
            .done(function(data) {
                //var thHTML='<thead><tr><th data-sortable="true" data-field="design_name"> design_name </th>
                // <th data-sortable="true" data-field="step_name"> step_name </th><th data-sortable="true" data-field="step_val">
                // step_val</th><th data-sortable="true" data-field="base_step"> base_step </th><th data-sortable="true" data-field="base_val">
                // base_val</th><th data-sortable="true" data-field="Gain-Loss"> Gain/Loss Pct.</th></tr></thead>'
                //$("#sqb_bs_table").append(thHTML)\
                debugger;
                // window.steps_list_dict = ["NWPOPT","NWCOPT","NWFOPT"];
                window.bs_data = [];
                if(data["result"]=="success"){
                    judgeEmpty = jQuery.parseJSON(data["step_qor_info"]);
                    if(isEmptyObject(judgeEmpty)){
                        warn.css("display","block");
                        warn.attr("class","alert alert-warning");
                        warn.append("<strong>Data</strong> do not exist");
                        l.stop();
                        return false;
                    }
                }
                else{
                    warn.css("display","block");
                    warn.attr("class","alert alert-danger");
                    warn.append(data["msg"]);
                    l.stop();
                    return false;
                }

                window.step_qor_info = jQuery.parseJSON(data["step_qor_info"]);
                // metrics = data['default_metrics'];
                info_index = []
                $.each(window.step_qor_info, function(value){
                    info_index.push(value)
                })
                metrics = info_index[0]
                console.log(window.step_qor_info);
                $.each(window.step_qor_info[metrics], function(design_name, value) {
                    if (value == "null") {
                        return true;
                    }
                    $.each(value, function(index, qor_data_list) {
                        //console.log(qor_data_list[0])
                        var dir = encodeURIComponent($("#sqt1-flow-dir").val());
                        var pattern = $("#tpattern").text().trim();
                        var stage = $("#tstage").text().trim().toLowerCase().substring(2, 6);
                        var reg = /\d+/;
                        var prevp = qor_data_list[0].match(reg);
                        var crntp = qor_data_list[2].match(reg);
                        var mt = "http://"+window.location.host+"/profile_"+ stage + "?mode=flow&compress=1&input_list=" + dir +"&cmd=" + stage +"&active_design=" + design_name+"&active_metrics=undefined&active_pattern=" + pattern + "&prev_d=0&prev_p=" + prevp + "&crnt_d=0&crnt_p="+ crntp ;
                        var data_ele = {
                            "design_name": design_name,
                            "step_name": qor_data_list[2],
                            "step_val": qor_data_list[3],
                            "base_name": qor_data_list[0],
                            "base_val": qor_data_list[1],
                            "pct": qor_data_list[4],
                            "link": "<a href='"+ mt +"'>View</a>"
                        }
                        window.bs_data.push(data_ele)
                        //$("#sqb_bs_table").append(trHTML)
                    })
                    //console.log(design_name)
                    //console.log(value)
                })
                $("#sqt-switch").text(metrics);
                $("#sqt-switch-li").empty();
                $.each(window.step_qor_info, function(metrics, dict) {
                    var li = "<li><a href='#' id='"+metrics+"' onclick='switchSqtMetrics(this);'>"+metrics+"</a></li>"
                    $("#sqt-switch-li").append(li);
                })
                var li = "<li><a href='#' id='summary' onclick='switchSqtNewMetrics(this);'>"+"SUMMARY"+"</a></li>"
                $("#sqt-switch-li").append(li);
                var distri_list = getDistriCount(window.bs_data);
//                      console.log(distri_list)

                myBarChart3.config.data.datasets[0].data = distri_list;
                myBarChart3.update();

                $('#sqt_bs_table').bootstrapTable('destroy').bootstrapTable({
                    //toolbar: '#toolbar',                //工具按钮用哪个容器
                    striped: true,                      //是否显示行间隔色
                    //cache: false,                       //是否使用缓存，默认为true，所以一般情况下需要设置一下这个属性（*）
                    pagination: true,                   //是否显示分页（*）
                    sortable: true,                     //是否启用排序
                    //sortOrder: "asc",                   //排序方式
                    //queryParams: oTableInit.queryParams,//传递参数（*）
                    //sidePagination: "server",           //分页方式：client客户端分页，server服务端分页（*）
                    pageNumber:1,                       //初始化加载第一页，默认第一页
                    pageSize: 50,                       //每页的记录行数（*）
                    pageList: [10, 25, 50, 100],        //可供选择的每页的行数（*）
                    search: true,
                    showExport: true,                    //是否显示导出
                    exportDataType: "all",
                    showColumns: true,
//                            showPaginationSwitch:true,
                    //strictSearch: true,
                    //clickToSelect: true,                //是否启用点击选中行
                    //height: 460,                        //行高，如果没有设置height属性，表格自动根据记录条数觉得表格高度
                    //uniqueId: "id",                     //每一行的唯一标识，一般为主键列
                    //cardView: false,                    //是否显示详细视图
                    //detailView: false,                   //是否显示父子表
                    columns: [{
                        field: 'design_name',
                        title: 'Design Name',
                        sortable: true
                    }, {
                        field: 'step_name',
                        title: 'Step Name',
                        sortable: true
                    }, {
                        field: 'step_val',
                        title: 'Step Value',
                        sortable: true
                    }, {
                        field: 'base_name',
                        title: 'Base Step',
                        sortable: true
                    }, {
                        field: 'base_val',
                        title: 'Base Value',
                        sortable: true
                    }, {
                        field: 'pct',
                        title: 'Percentage (%)',
                        sortable: true
                    },{
                        field: 'link',
                        title: 'Profile link',
                        sortable: true,
                    }
                    ],
                    data: window.bs_data
                });

                //$('#sqb_bs_table')
                // $("#sqb1-step-name").css("display","block");
                // $("#stage").css("display","block");
                $("#sqt-hide").css("display","block");
                $(".sqt-chart").css("display","block");
                $(".sqt-switch").css("display", "table");
                console.log("success!");
                l.stop();
            })
            .fail(function() {
                //$(destId).text("Error: Could not contact server.");
                l.stop();
                console.log("fail!")
            });
    })

    $('#sqa_btn').click(function(e) {
        //$(".gain-loss-display").css("display","none");
        var l = Ladda.create(this);
        l.start();
        $.post('analysis_sqa', {
            flowb_dir: $("#sqa1-flowb-dir").val(),
            flowc_dir: $("#sqa1-flowc-dir").val(),
        }, function () {
            console.log("sending post...")
        })
            .done(function(data) {
                window.bs_data = []
                $(".sqa").css("display","none");

                console.log("success!")
                l.stop();
            })
            .fail(function() {
                l.stop();
                console.log("fail!")
            });
    })
});

//cmd stats
var ctx = $("#myChart").get(0).getContext("2d");
// This will get the first returned node in the jQuery collection.
var data1 = {
    labels: ["-100%+", "-100%", "(-100%~-80%]", "(-80%+~-50%]","(-50%~-20%]", "(-20%~-10%]", "(-10%~-0%)", "0%", "(+0%~+10%)", "[+10%~+20%)", "[+20%~+50%)", "[+50%~+80%)", "[+80%~+100%)", "+100%", "+100%+"],
    datasets: [
        {
            label: "qor distribution",
            backgroundColor: [
                'rgba(153, 204, 51, 1)',
                'rgba(153, 204, 51, 0.9)',
                'rgba(153, 204, 51, 0.8)',
                'rgba(153, 204, 51, 0.6)',
                'rgba(153, 204, 51, 0.5)',
                'rgba(153, 204, 51, 0.3)',
                'rgba(153, 204, 51, 0.1)',
                'rgba(119, 119, 119, 0.2)',
                'rgba(255, 99, 132, 0.1)',
                'rgba(255, 99, 132, 0.3)',
                'rgba(255, 99, 132, 0.5)',
                'rgba(255, 99, 132, 0.6)',
                'rgba(255, 99, 132, 0.8)',
                'rgba(255, 99, 132, 0.9)',
                'rgba(255, 99, 132, 1)',
                //'rgba(255, 99, 132, 0.2)',
                //'rgba(54, 162, 235, 0.2)',
                //'rgba(255, 206, 86, 0.2)',
                //'rgba(75, 192, 192, 0.2)',
                //'rgba(153, 102, 255, 0.2)',
                //'rgba(255, 159, 64, 0.2)'
            ],
            borderColor: [
                'rgba(75, 192, 192, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(119, 119, 119, 0.8)',
                'rgba(255,99,132,1)',
                'rgba(255,99,132,1)',
                'rgba(255,99,132,1)',
                'rgba(255,99,132,1)',
                'rgba(255,99,132,1)',
                'rgba(255,99,132,1)',
                'rgba(255,99,132,1)',
                //'rgba(54, 162, 235, 1)',
                //'rgba(255, 206, 86, 1)',
                //'rgba(75, 192, 192, 1)',
                //'rgba(153, 102, 255, 1)',
                //'rgba(255, 159, 64, 1)'
            ],
            borderWidth: 1,
            data: [65, 59, 80, 81, 56, 55, 40, 22, 45, 68, 34, 67 ,67, 23, 88],
        },
    ],
};

Chart.pluginService.register({
    beforeRender: function (chart) {
        if (chart.config.options.showAllTooltips) {
            // create an array of tooltips
            // we can't use the chart tooltip because there is only one tooltip per chart
            chart.pluginTooltips = [];
            chart.config.data.datasets.forEach(function (dataset, i) {
                chart.getDatasetMeta(i).data.forEach(function (sector, j) {
                    chart.pluginTooltips.push(new Chart.Tooltip({
                        _chart: chart.chart,
                        _chartInstance: chart,
                        _data: chart.data,
                        _options: chart.options.tooltips,
                        _active: [sector]
                    }, chart));
                });
            });

            // turn off normal tooltips
            chart.options.tooltips.enabled = false;
        }
    },
    afterDraw: function (chart, easing) {
        if (chart.config.options.showAllTooltips) {
            // we don't want the permanent tooltips to animate, so don't do anything till the animation runs atleast once
            if (!chart.allTooltipsOnce) {
                if (easing !== 1)
                    return;
                chart.allTooltipsOnce = true;
            }

            // turn on tooltips
            chart.options.tooltips.enabled = true;
            Chart.helpers.each(chart.pluginTooltips, function (tooltip) {
                console.log(chart.data);
                //tooltip.initialize();
                //tooltip.update();
                // we don't actually need this since we are not animating tooltips
                //tooltip.pivot();
                //tooltip.transition(easing).draw();
            });
            //chart.options.tooltips.enabled = false;
        }
    }
})

var myBarChart = new Chart(ctx, {
    type: 'bar',
    data: data1,
    options: {
        showAllTooltips: true,
        legend: {
            display: false,
        },
        tooltips: {
            callbacks: {
                label: function(tooltipItem, data) {
                    var allData = data.datasets[tooltipItem.datasetIndex].data;
                    var tooltipLabel = data.labels[tooltipItem.index];
                    var tooltipData = allData[tooltipItem.index];
                    var total = 0;
                    for (var i in allData) {
                        total += allData[i];
                    }
                    var tooltipPercentage = Math.round((tooltipData / total) * 100);
                    return tooltipData + ' (' + tooltipPercentage + '%)';
                },
            }
        },
        scales: {
            xAxes: [{
                stacked: true
            }],
            yAxes: [{
                stacked: true
            }]
        },
    }
});

$("#myChart").click(function (evt) {
    var filter_data = {};
    var index_data = {};
    var activePoints = myBarChart.getElementAtEvent(evt.originalEvent);
    if(activePoints!=""){
        var distri_index = activePoints[0]._index;
        index_data = filterDistriCount(window.bs_data);
        filter_data = index_data[distri_index];
        console.log(distri_index);
    }
    else{
        filter_data = window.bs_data;
    }
    $('#sqb_bs_table').bootstrapTable('destroy').bootstrapTable({
        //toolbar: '#toolbar',                //工具按钮用哪个容器
        striped: true,                      //是否显示行间隔色
        //cache: false,                       //是否使用缓存，默认为true，所以一般情况下需要设置一下这个属性（*）
        pagination: true,                   //是否显示分页（*）
        sortable: true,                     //是否启用排序
        pageNumber:1,                       //初始化加载第一页，默认第一页
        pageSize: 50,                       //每页的记录行数（*）
        pageList: [10, 25, 50, 100],        //可供选择的每页的行数（*）
        search: true,
        showExport: true,                    //是否显示导出
        exportDataType: "all",
        showColumns: true,
        columns: [{
            field: 'design_name',
            title: 'Design Name',
            sortable: true
        }, {
            field: 'step_name',
            title: 'Step Name',
            sortable: true
        }, {
            field: 'step_val',
            title: 'Step Value',
            sortable: true
        }, {
            field: 'base_name',
            title: 'Base Step',
            sortable: true
        }, {
            field: 'base_val',
            title: 'Base Value',
            sortable: true
        }, {
            field: 'pct',
            title: 'Percentage (%)',
            sortable: true
        },{
            field: 'link',
            title: 'Profile link',
            sortable: true
        }
        ],
        data: filter_data
    })
});
