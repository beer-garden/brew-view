import angular from 'angular';

requestIndexController.$inject = [
  '$scope',
  'DTOptionsBuilder',
  'DTColumnBuilder',
  'DTRendererService',
  'RequestService',
];

/**
 * requestIndexController - Angular controller for viewing all requests.
 * @param  {$scope} $scope            Angular's $scope object.
 * @param  {Object} DTOptionsBuilder  Data-tables' options builder object.
 * @param  {Object} DTColumnBuilder   Data-tables' column builder object.
 * @param  {Object} DTRendererService Data-tables' rendering service.
 * @param  {Object} RequestService    Beer-Garden Request Service.
 */
export default function requestIndexController(
  $scope,
  DTOptionsBuilder,
  DTColumnBuilder,
  DTRendererService,
  RequestService) {
  $scope.requests = {};
  $scope.requests.errorMap = RequestService.errorMap;

  $scope.dtOptions = DTOptionsBuilder.newOptions()
    .withOption('autoWidth', false)
    .withOption('ajax', function(data, callback, settings) {
      // Need to also request ID for the href
      data.columns.push({'data': 'id'});

      RequestService.getRequests(data).then(
        function(response) {
          $scope.requests.loaded = true;
          $scope.requests.error = false;
          $scope.requests.status = response.status;
          $scope.requests.errorMessage = '';

          callback({
            data: response.data,
            draw: response.headers('draw'),
            recordsFiltered: response.headers('recordsFiltered'),
            recordsTotal: response.headers('recordsTotal'),
          });
        },
        function(response) {
          $scope.requests.loaded = false;
          $scope.requests.error = true;
          $scope.requests.status = response.status;
          $scope.requests.errorMessage = response.data.message;
        }
      );
    })
    .withLightColumnFilter({
      0: {html: 'input', type: 'text', attr: {class: 'form-inline form-control'}},
      1: {html: 'input', type: 'text', attr: {class: 'form-inline form-control'}},
      2: {
        html: 'select',
        type: 'text',
        cssClass: 'form-inline form-control',
        values: [
          {value: '', label: ''},
          {value: 'CREATED', label: 'CREATED'},
          {value: 'RECEIVED', label: 'RECEIVED'},
          {value: 'IN_PROGRESS', label: 'IN PROGRESS'},
          {value: 'CANCELED', label: 'CANCELED'},
          {value: 'SUCCESS', label: 'SUCCESS'},
          {value: 'ERROR', label: 'ERROR'},
        ],
      },
      3: {
        html: 'range', type: 'text',
        attr: {class: 'form-inline form-control', style: 'width: 50%;'},
      },
      4: {html: 'input', type: 'text', attr: {class: 'form-inline form-control'}},
    })
    .withDataProp('data')
    .withOption('order', [3, 'desc'])
    .withOption('serverSide', true)
    .withPaginationType('full_numbers')
    .withBootstrap();

  $scope.dtColumns = [
    DTColumnBuilder
      .newColumn('command')
      .withTitle('Command Name')
      .renderWith(function(data, type, full) {
        return '<a href="#!/requests/' + full.id + '">' + data + '</a>';
      }),
    DTColumnBuilder
      .newColumn('system')
      .withTitle('System')
      .renderWith(function(data, type, full) {
        let systemName = data;
        if (full['metadata'] && full['metadata']['system_display_name']) {
          systemName = full['metadata']['system_display_name'];
        }

        if (angular.isDefined(full.instance_name) && full.instance_name !== null) {
          return systemName + ' [' + full.instance_name + ']';
        } else {
          return systemName;
        }
      }),
    DTColumnBuilder
      .newColumn('status')
      .withTitle('Status'),
    DTColumnBuilder
      .newColumn('created_at')
      .withTitle('Created')
      .withOption('type', 'date')
      .withOption('width', '25%')
      .renderWith(function(data, type, full) {
        return new Date(data);
      }),
    DTColumnBuilder
      .newColumn('comment')
      .withTitle('Comment'),
    DTColumnBuilder
      .newColumn('metadata')
      .notVisible(),
  ];

  DTRendererService.registerPlugin({
    postRender: function(options, result) {
      // Insert our spinner thingy next to the search box
      let spinner = $('<span>').addClass('spinner');
      $('.dataTables_filter label').prepend(spinner);

      // Register callback to show / hide spinner thingy
      let processingDelay = null;
      $('.dataTable').on('processing.dt', function(e, settings, processing) {
        if (!processing) {
          clearTimeout(processingDelay);
          spinner.css('visibility', 'hidden');
        } else {
          processingDelay = setTimeout(function() {
            spinner.css('visibility', 'visible');
          }, 500);
        }
      });
    },
  });
};
