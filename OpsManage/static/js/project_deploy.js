function changeEnv(e) {
    var url = $(e).data().http,
        dbId = $(e).data().id;
    $(e).addClass('btn-primary').removeClass('btn-default').siblings().addClass('btn-default').removeClass('btn-primary');
    $.ajax({
        url: url,
        type: "GET",
        async: false,
        data: {"id": dbId},
        dataType: "json",
        success: function (result) {
            $(e).parent().next().html(template('childTmp', result))
        }
    });
}

function deleteProject(obj, id) {
    var txt = "是否确认删除？";
    var btnObj = $(obj);
    btnObj.attr('disabled', true);
    var option = {
        title: "删除任务",
        btn: parseInt("0011", 2),
        onOk: function () {
            $.ajax({
                type: 'DELETE',
                url: '/api/deploy_v2/' + id + '/',
                success: function (response) {
                    btnObj.removeAttr('disabled');
                    window.wxc.xcConfirm("删除成功！", window.wxc.xcConfirm.typeEnum.success);
                    location.reload('/deploy_list/');
                },
                error: function (response) {
                    btnObj.removeAttr('disabled');
                    window.wxc.xcConfirm("删除失败！" + response, window.wxc.xcConfirm.typeEnum.error);
                }
            });
        },
        onCancel: function () {
        },
        onClose: function () {
        }
    }
    window.wxc.xcConfirm(txt, "custom", option);
}

function projcectVersion(obj, model, id, op) {
    var btnObj = $(obj);
    btnObj.attr('disabled', true);
    if (op == 'create') {
        txt = "请输入要创建的分支：";
    }
    else {
        txt = "请输入要删除的分支：";
    }
    ;
    window.wxc.xcConfirm(txt, window.wxc.xcConfirm.typeEnum.input, {
        onOk: function (result) {
            if (result.length == 0) {
                /* 如果没有输入字符串则直接退出 */
                return;
            };
            $.ajax({
                type: 'POST',
                url: '/deploy_version/' + id + '/',
                data: {
                    "model": model,
                    'name': result,
                    'op': op,
                },
                success: function (response) {

                    if (response["code"] == "200") {
                        window.wxc.xcConfirm(response["msg"], window.wxc.xcConfirm.typeEnum.success);
                    }
                    else {
                        window.wxc.xcConfirm("分支操作错误：" + response["msg"], window.wxc.xcConfirm.typeEnum.error);
                    }
                    ;
                    btnObj.removeAttr('disabled');
                },
                error: function (response) {
                    btnObj.removeAttr('disabled');
                    window.wxc.xcConfirm("创建分支失败", window.wxc.xcConfirm.typeEnum.error);
                },
            });

        }
    });
}

function search_go() {
    var parameter = {};
    $("input[type='hidden']").each(function () {
        var key = $(this).prop('name');
        var value = $(this).val();
        if (key != "csrfmiddlewaretoken") {
            parameter[key] = value;
        }
    })

    var count = 0;
    for (var i in parameter) {
        count += i;
        break;
    }
    if (count == 0) {
        return false;
    }

    $.post('/new_deploy_search/', parameter, function (result) {
        if (result["data"].length > 0) {
            /*                 	document.getElementById("div-search-result").style.display = ""; */
            var table = $('#deployTableList').dataTable();
            oSettings = table.fnSettings();
            table.fnClearTable(this);
            for (var i = 0; i < result["data"].length; i++) {
                table.oApi._fnAddData(oSettings, result["data"][i]);
            }
            oSettings.aiDisplay = oSettings.aiDisplayMaster.slice();
            table.fnDraw();
        }
        else {
            //没有数据就清空
            var table = $('#deployTableList').dataTable();
            table.fnClearTable(this);
        }
    })
}

function changepage(pageindex) {
    curpage = pageindex;
    search_go();
}

function removeself(obj) {
    $(obj).parent().remove();
    changepage(1);
}

function initProject(obj, name, id) {
    var txt = "是否确认初始化（" + name + "）";
    var btnObj = $(obj);
    btnObj.attr('disabled', true);
    var option = {
        title: "初始化项目",
        btn: parseInt("0011", 2),
        onOk: function () {
            $('#deployCompileModal').modal('show');
            runCompile(obj,id)
        },
        onCancel: function () {
            btnObj.removeAttr('disabled');
        },
        onClose: function () {
            btnObj.removeAttr('disabled');
        }
    }
    window.wxc.xcConfirm(txt, "custom", option);
}


function runCompile(obj,id) {
    $("#result").html("服务器正在处理，请稍等。。。");
    var data = $(obj).data().uuid;
    /* 轮训获取结果 开始  */

    var interval = setInterval(function () {
        $.ajax({
            url: '/deploy_result/'+id+'/',
            type: 'post',
            data: {
                project_uuid: data
            },
            success: function (result) {
                if (result["msg"] !== null) {
                    $("#result").append("<p>" + result["msg"] + "</p>");
                    if (result["msg"].indexOf("[Done]") == 0) {
                        $('#deployCompileModal').modal('hide');
                        clearInterval(interval);
                        window.wxc.xcConfirm("编译成功", window.wxc.xcConfirm.typeEnum.success);
                    }
                }
            }
        });
    }, 1000);

    /* 轮训获取结果结束  */
    $.ajax({
        url: '/deploy_compile/'+id +'/', //请求编译打包地址
        type: "POST",  //提交类似
        success: function (response) {
            if (response["code"] == "500") {
                $('#deployCompileModal').modal('hide');
                clearInterval(interval);
                $('#result').append('<p class="text-danger">编译失败:'+ response["msg"]+'</p>')
            }
        },
        error: function (response) {
            $('#result').append('<p class="text-danger">编译失败:'+ response["msg"]+'</p>')
            clearInterval(interval);
        }
    })
}
