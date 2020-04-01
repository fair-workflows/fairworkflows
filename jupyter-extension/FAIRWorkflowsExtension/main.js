define([
    'base/js/namespace',
    'base/js/events'
], function(Jupyter, events) {

    // Button to add FAIR buttons
    var add_FAIR_buttons = function () {

        // Add cell toolbars button
        var add_buttons_to_celltoolbar = function(div, cell) {

            // Publish step button
            var button_step = $('<button/>').addClass('fa fa-ship');
            button_step.click(function(){
                    button_step.text("Published!");
                    publish_FAIR_step();
            })
            $(div).append(button_step);

            // FAIRify data button
            var button_data = $('<button/>').addClass('fa fa-check');
            button_data.click(function(){
                    button_data.text("Data FAIRified!");
                    fairify_data();
            })
            $(div).append(button_data);
        }
        Jupyter.CellToolbar.register_callback('FAIRcell', add_buttons_to_celltoolbar)
        Jupyter.CellToolbar.global_show()

        Jupyter.CellToolbar.register_preset('FAIRWorkflows',['FAIRcell'])
        Jupyter.CellToolbar.activate_preset('FAIRWorkflows')

        // Add publish workflow button
        Jupyter.toolbar.add_buttons_group([
            Jupyter.keyboard_manager.actions.register ({
                'help': 'Publish as FAIR Workflow',
                'icon': 'fa-ship',
                'handler': publish_FAIR_workflow
            }, 'publish-FAIR-workflow', 'FAIR Workflows'),
            Jupyter.keyboard_manager.actions.register ({
                'help': 'Add manual step',
                'icon': 'fa-user-o',
                'handler': add_manual_step
            }, 'add-manual-FAIR-step', 'FAIR Workflows')
        ])
    }

    // Run on start
    function load_ipython_extension() {
        add_FAIR_buttons();
    }

    // Publish the selected cell
    var publish_FAIR_step = function() {
        var cell = Jupyter.notebook.get_selected_cell();
        var cell_index = Jupyter.notebook.get_selected_index();
        step_rdf = cell.get_text()

        Jupyter.notebook.insert_cell_below('markdown', cell_index).set_text(step_rdf);
    };

    // Add a new manual step cell
    var add_manual_step = function() {
        var cell = Jupyter.notebook.get_selected_cell();
        var cell_index = Jupyter.notebook.get_selected_index();

        cell.metadata.manual_step = true;
        default_manual_text = "#Manual Step\n\n1. _ \n2. _ \n3. ...";
        Jupyter.notebook.insert_cell_below('markdown', cell_index).set_text(default_manual_text);
    };

    // Publish the whole workflow
    var publish_FAIR_workflow = function() {
        var num_cells = Jupyter.notebook.get_cells().length;
        alert('Workflow published! Consisted of ' + num_cells + ' steps.');
    };

    // FAIRify the data in the cell
    var fairify_data = function() {
        alert("FAIRifying data");
    };

    return {
        load_ipython_extension: load_ipython_extension
    };
});

