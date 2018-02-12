import angular from 'angular';

systemViewController.$inject = [
  '$scope',
  '$stateParams',
  '$interval',
  'SystemService',
  'CommandService',
  'UtilityService',
  'DTOptionsBuilder',
];

/**
 * systemViewController - Angular Controller for viewing a single system.
 * @param  {$scope} $scope             Angular's $scope object.
 * @param  {$stateParams} $stateParams Angular's $stateParams object.
 * @param  {$interval} $interval       Angular's $interval object.
 * @param  {Object} SystemService      Beer-Garden System Service.
 * @param  {Object} CommandService     Beer-Garden Command Service.
 * @param  {Object} UtilityService     Beer-Garden Utility Service.
 * @param  {Object} DTOptionsBuilder   Object for building Data-Tables objects.
 */
export default function systemViewController(
  $scope,
  $stateParams,
  $interval,
  SystemService,
  CommandService,
  UtilityService,
  DTOptionsBuilder) {
  $scope.util = UtilityService;

  $scope.system = {
    data: {},
    loaded: false,
    error: false,
    errorMessage: '',
    forceReload: false,
    status: null,
    errorMap: {
      'empty': {
        'solutions': [
          {
            problem: 'ID is incorrect',
            description: 'The Backend has restarted and the ID changed of the system you ' +
                         'were looking at',
            resolution: 'Click the ' + $scope.config.applicationName + ' logo at the top ' +
                        'left and refresh the page',
          },
          {
            problem: 'The Plugin Stopped',
            description: 'The plugin could have been stopped. You should probably contact the ' +
                         'plugin maintainer. You should be able to tell what\'s wrong by their ' +
                         'logs. Plugins are located at <code>$APP_HOME/plugins</code>',
            resolution: '<kbd>less $APP_HOME/log/my-plugin.log</kbd>',
          },
        ],
      },
    },
  };

  $scope.dtOptions = DTOptionsBuilder.newOptions()
    .withOption('order', [4, 'asc'])
    .withOption('autoWidth', false)
    .withBootstrap();

  $scope.successCallback = function(response) {
    $scope.system.data = response.data;
    $scope.system.loaded = true;
    $scope.system.error = false;
    $scope.system.status = response.status;
    $scope.system.errorMessage = '';
  };

  $scope.failureCallback = function(response) {
    $scope.system.data = {};
    $scope.system.loaded = false;
    $scope.system.error = true;
    $scope.system.status = response.status;
    $scope.system.errorMessage = data.message;
  };

  // Register a function that polls if the system is in a transition status
  let statusUpdate = $interval(function() {
    if (['STOPPING', 'STARTING'].indexOf($scope.system.data.status) != -1) {
      SystemService.getSystem(
        $scope.system.data.id, false,
        function(data, status, headers, config) {
          $scope.system.data.status = data.status;
      });
    }
  }, 1000);

  $scope.$on('$destroy', function() {
    if (angular.isDefined(statusUpdate)) {
      $interval.cancel(statusUpdate);
      statusUpdate = undefined;
    }
  });

  SystemService.getSystem($stateParams.id, true)
    .then($scope.successCallback, $scope.failureCallback);
};
