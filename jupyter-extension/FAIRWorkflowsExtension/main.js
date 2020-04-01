define([
    'base/js/namespace',
    'base/js/events'
], function(Jupyter, events) {

    // Button to add FAIR buttons
    var add_FAIR_buttons = function () {

        // Add publish cell button
        var toggle = function(div, cell) {
            var button = $('<button/>').addClass('fa fa-ship');
            button.click(function(){
                    button.text("Published!");
                    publish_FAIR_step();
            })
            $(div).append(button);            
        }




        Jupyter.CellToolbar.register_callback('FAIRcell', toggle)
        Jupyter.CellToolbar.global_show()

        Jupyter.CellToolbar.register_preset('FAIRWorkflows',['FAIRcell'])
        Jupyter.CellToolbar.activate_preset('FAIRWorkflows')

        // Add publish workflow button
        Jupyter.toolbar.add_buttons_group([
            Jupyter.keyboard_manager.actions.register ({
                'help': 'Publish as FAIR Workflow',
                'icon': 'fa-ship',
                'handler': publish_FAIR_workflow
            }, 'publish-FAIR-workflow', 'Publish Workflow')
        ])
    }

    // Run on start
    function load_ipython_extension() {
        add_FAIR_buttons();
    }

    // Publish the selected cell
    var publish_FAIR_step = function() {
        var cell = Jupyter.notebook.get_selected_cell();
        alert('Step published!\n' + cell.get_text());
    };

    // Publish the whole workflow
    var publish_FAIR_workflow = function() {
        var num_cells = Jupyter.notebook.get_cells().length
        alert('Workflow published! Consisted of ' + num_cells + ' steps.');
    };

    return {
        load_ipython_extension: load_ipython_extension
    };
});

