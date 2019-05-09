
commandIndexController.$inject = [
  '$rootScope',
  '$scope',
  '$q',
  'SystemService',
  'CommandService',
  'DTOptionsBuilder',
];

/**
 * commandIndexController - Angular controller for all commands page.
 * @param  {$rootScope} $rootScope   Angular's $rootScope object.
 * @param  {$scope} $scope           Angular's $scope object.
 * @param  {$q} $q                   Angular's $q object.
 * @param  {Object} SystemService    Beer-Garden system service.
 * @param  {Object} CommandService   Beer-Garden command service.
 * @param  {Object} DTOptionsBuilder Data-tables' builder for options.
 */
export default function commandIndexController(
  $rootScope,
  $scope,
  $q,
  SystemService,
  CommandService,
  DTOptionsBuilder) {
  $scope.setWindowTitle('commands');

  $scope.dtOptions = DTOptionsBuilder.newOptions()
    .withOption('order', [4, 'asc'])
    .withOption('autoWidth', false)
    .withBootstrap();

  $scope.stateParams = function(entry) {
    return {
      id: entry.id,
      name: entry.name,
      systemName: entry.system,
      systemVersion: $rootScope.getVersionForUrl(entry.version),
    };
  };

  $scope.successCallback = function(response) {
    let systems = response['systems'].data;
    let commands = [];

    // Sort the systems
    systems.sort((a, b) => {
      let aName = a.display_name || a.name;
      let bName = b.display_name || b.name;

      if (aName < bName) return -1;
      if (aName > bName) return 1;
      return 0;
    });

    systems.forEach((system) => {
      // Sort the commands
      system.commands.sort((a, b) => {
        if (a.name < b.name) return -1;
        if (a.name > b.name) return 1;
        return 0;
      });

      // Then pull out what we care about
      system.commands.forEach((command) => {
        commands = commands.concat({
          id: command.id,
          name: command.name,
          system: system.name,
          version: system.version,
          description: command.description || 'No Description Provided',
        });
      });
    });

    $scope.response = response['systems'];
    $scope.data = commands;
  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.data = {};
  };

  const loadCommands = function() {
    $scope.response = undefined;
    $scope.data = {};

    $rootScope.systemsPromise.then(
      () => {
        // We don't actually use the CommandService.getCommands(), but make the
        // call just to verify that the user has bg-command-read
        $q.all({
          commands: CommandService.getCommands($scope.currentNamespace()),
          systems: SystemService.getSystems($scope.currentNamespace()),
        }).then(
          $scope.successCallback,
          $scope.failureCallback
        );
      },
      $scope.failureCallback
    );
  };

  $scope.$on('userChange', function() {
    loadCommands();
  });

  loadCommands();
};
