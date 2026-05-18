% Define the data
rs = [62.39, 62.86, 63.32, 63.81, 64.25];
m1 = [63.06, 63.53, 64.04, 64.53, 65.02];
m2 = [62.39, 62.84, 63.33, 63.81, 64.28];

% Put them in a cell array for easy looping
datasets = {rs, m1, m2};
names = {'Run Steps', 'Song Beats (before PP)', 'Song Beats (after PP)'};
colors = {[0 0.4470 0.7410], [0.8500 0.3250 0.0980], [0.290 1.0 0.1250]};

% 1. Find the global min and max across ALL data to force a shared axis scale
all_data = [rs, m1, m2];
global_xlim = [min(all_data) - 0.3, max(all_data) + 0.3]; 

figure;

% --- TWEAK 1: Create a tiled layout and set 'TileSpacing' to 'loose' ---
% Options are 'loose', 'compact', or 'tight'. 'loose' maximizes the gap.
t = tiledlayout(3, 1, 'TileSpacing', 'loose'); 

for i = 1:3
    % --- TWEAK 2: Replace subplot with nexttile ---
    nexttile; 
    
    current_data = datasets{i};
    
    % Plot 1D points: X is the data value, Y is always 0
    y_zeros = zeros(size(current_data));
    plot(current_data, y_zeros, 'o', 'MarkerSize', 10, ...
         'MarkerFaceColor', colors{i}, 'MarkerEdgeColor', 'k');
    
    hold on;
    
    % Draw the aligned timeline baseline across the entire shared range
    line(global_xlim, [0, 0], 'Color', [0.6 0.6 0.6], 'LineWidth', 1);
    
    % Add text labels directly above each stamped point
    for j = 1:length(current_data)
        text(current_data(j), 0.05, num2str(current_data(j)), ...
            'HorizontalAlignment', 'center', 'VerticalAlignment', 'bottom', ...
            'FontSize', 9, 'FontWeight', 'bold');
    end
    
    % Styling and layout rules
    title([ names{i}]);
    xlim(global_xlim);   % <-- Enforces the identical horizontal scale
    ylim([-0.2, 0.4]);   % Breeding room for the text labels
    xlabel("t [sec]")
    
    % Hide the Y-axis and box borders completely
    ax = gca;
    ax.YAxis.Visible = 'off';   
    ax.Box = 'off';             
    
    % Only keep the X-axis tick lines visible on the bottom plot to keep it clean
    if i < 3
        ax.XAxis.TickLength = [0 0]; % Optional: hides tick marks for cleaner look on top plots
    end
end

% --- TWEAK 3: Update sgtitle to apply to the tiled layout ---
title(t, 'Beat Alignment', 'FontSize', 14, 'FontWeight', 'bold');