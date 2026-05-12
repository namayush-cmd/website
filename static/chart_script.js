
var option = {
    tooltip: {},
    xAxis3D: {
        type: 'category',
        data: ['Central', 'State', 'Total']
    },
    yAxis3D: {
        type: 'category',
        data: ['Recurring', 'Non-Recurring']
    },
    zAxis3D: {
        type: 'value'
    },
    visualMap: {
        max: 5000,
        inRange: {
            color: ['#00f', '#0ff', '#0f0', '#ff0', '#f00']
        }
    },
    series: [{
        type: 'bar3D',
        data: [
            [0,0,getVal("b_c_util_r")],
            [0,1,getVal("b_c_util_nr")],
            [1,0,getVal("b_s_util_r")],
            [1,1,getVal("b_s_util_nr")],
            [2,0,getVal("b_t_util_r")],
            [2,1,getVal("b_t_util_nr")]
        ]
    }]
};

chart.setOption(option);