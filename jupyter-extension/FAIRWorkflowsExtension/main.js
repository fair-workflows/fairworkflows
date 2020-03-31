define([
    'base/js/namespace',
    'base/js/events'
], function(Jupyter, events) {

      // Button to add default cell
    var add_publish_FAIR_workflow_button = function () {
        Jupyter.toolbar.add_buttons_group([
            Jupyter.keyboard_manager.actions.register ({
                'help': 'Publish as FAIR Workflow',
                'icon': 'fa-comment-o',
                'handler': publish_FAIR_workflow
            }, 'publish-FAIR-workflow', 'Publish Workflow')
      ])
    }

    // Run on start
    function load_ipython_extension() {
        add_publish_FAIR_workflow_button();
    }

    // Publish the whole workflow
    var publish_FAIR_workflow = function() {
        alert('Workflow published!');
    };

    return {
        load_ipython_extension: load_ipython_extension
    };
});

