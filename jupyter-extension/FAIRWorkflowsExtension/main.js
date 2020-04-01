define([
    'base/js/namespace',
    'base/js/events'
], function(Jupyter, events) {

    // Button to add FAIR buttons
    var add_FAIR_buttons = function () {

        // Add cell toolbar buttons
        var add_buttons_to_celltoolbar = function(div, cell) {

            // (Hopefully) intelligent search button
            var button_search = $('<button/>').addClass('fa fa-search');
            button_search.click(function(){
                    var text = cell.get_text()
                    result = search_FAIR_steps(text);
                    button_search.text(result);
            })
            $(div).append(button_search);
        }
        Jupyter.CellToolbar.register_callback('FAIRcell', add_buttons_to_celltoolbar)
        Jupyter.CellToolbar.global_show()

        Jupyter.CellToolbar.register_preset('FAIRWorkflows',['FAIRcell'])
        Jupyter.CellToolbar.activate_preset('FAIRWorkflows')

        // Add FAIR Workflows related buttons
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
            }, 'add-manual-FAIR-step', 'FAIR Workflows'),
            Jupyter.keyboard_manager.actions.register ({
                'help': 'Package as CWL tool',
                'icon': 'fa-archive',
                'handler': add_manual_step
            }, 'package_as_cwl_tool', 'FAIR Workflows')
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
        default_manual_text = "# Manual Step\n\n1. _ \n2. _ \n3. ...";
        Jupyter.notebook.insert_cell_below('markdown', cell_index).set_text(default_manual_text);
    };

    // Publish the whole workflow
    var publish_FAIR_workflow = function() {
        var num_cells = Jupyter.notebook.get_cells().length;
        alert('Workflow published! Consisted of ' + num_cells + ' steps.');
    };

    // Search for FAIR steps matching this text
    var search_FAIR_steps = function(text) {
        return "    Searching for '" + text + "'";
    };

    return {
        load_ipython_extension: load_ipython_extension
    };
});

