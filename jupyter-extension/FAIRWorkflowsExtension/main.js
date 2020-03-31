define([
    'base/js/namespace',
    'base/js/events'
], function(Jupyter, events) {

    // Button to add default cell
    var add_FAIR_buttons = function () {

        // Add publish cell button
        Jupyter.toolbar.add_buttons_group([
            Jupyter.keyboard_manager.actions.register ({
                'help': 'Publish cell as FAIR step',
                'icon': 'fa-truck',
                'handler': publish_FAIR_step
            }, 'publish-FAIR-workflow', 'Publish Step')
        ])

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
        alert('Step published!');
    };

    // Publish the whole workflow
    var publish_FAIR_workflow = function() {
        alert('Workflow published!');
    };

    return {
        load_ipython_extension: load_ipython_extension
    };
});

