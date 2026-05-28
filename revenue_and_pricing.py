import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def plot_complete_assignment(pc=1.5, pr=2.5, max_v=4):
    """
    Plots the complete willingness-to-pay space covering Exercises 2, 3, and 4.
    pc: price of chocolate croissant
    pr: price of regular croissant
    max_v: upper limit of the uniform distribution
    """
    fig, ax = plt.subplots(figsize=(11, 9))
    
    # Draw the outer 4x4 box
    ax.plot([0, max_v, max_v, 0, 0], [0, 0, max_v, max_v, 0], color='black', linewidth=1.5)
    
    # Define colors for Ex 4 final purchasing areas
    color_none = '#E0E0E0' # Gray
    color_reg = '#BBDEFB'  # Blue
    color_choc = '#FFCDD2' # Pink/Red
    
    # ---------------------------------------------------------
    # Fill Ex 4 Areas
    # ---------------------------------------------------------
    # Area (i) No Purchase
    ax.fill_between([0, pc], 0, pr, color=color_none)
    
    # Area (ii) Buy Regular
    ax.fill_between([0, pc], pr, max_v, color=color_reg)
    ax.fill([pc, pc, max_v - (pr - pc)], [pr, max_v, max_v], color=color_reg)
    
    # Area (iii) Buy Chocolate
    ax.fill_between([pc, max_v], 0, pr, color=color_choc)
    ax.fill([pc, max_v - (pr - pc), max_v, max_v], [pr, max_v, max_v, pr], color=color_choc)
    
    # ---------------------------------------------------------
    # Draw lines (Ex 2 & Ex 3)
    # ---------------------------------------------------------
    # Ex 2: Price Lines
    ax.plot([pc, pc], [0, max_v], color='black', linestyle='--', linewidth=2, alpha=0.7)
    ax.plot([0, max_v], [pr, pr], color='black', linestyle='--', linewidth=2, alpha=0.7)
    
    # Ex 3: Indifference Line
    ax.plot([pc, max_v - (pr - pc)], [pr, max_v], color='green', linewidth=3, label=r'Ex 3: Indifference Line ($u_r = u_c$)')
    
    # ---------------------------------------------------------
    # Annotations for Ex 2 Regions
    # ---------------------------------------------------------
    ax.text(pc/2, pr/2, "Ex 2:  (i)\n$u_r < 0$, $u_c < 0$", ha='center', va='center', fontsize=11)
    ax.text(pc/2, (pr+max_v)/2, "Ex 2:  (ii)\n$u_r > 0$, $u_c < 0$", ha='center', va='center', fontsize=11)
    ax.text((pc+max_v)/2, pr/2, "Ex 2:  (iii)\n$u_c > 0$, $u_r < 0$", ha='center', va='center', fontsize=11)
    
    # Region (iv) is split by the indifference line
    ax.text((pc+max_v)/2 + 0.2, (pr+max_v)/2 - 0.2, 
            "Ex 2: (iv)\n$u_r > 0$, $u_c > 0$\n(Split by Indifference Line)", 
            ha='center', va='center', fontsize=11, 
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray', boxstyle='round,pad=0.5'))

    # Label the price lines with variables
    ax.text(pc - 0.1, max_v + 0.1, r'$p_c$', color='black', fontsize=14, ha='center')
    ax.text(max_v + 0.1, pr - 0.05, r'$p_r$', color='black', fontsize=14, va='center')

    # ---------------------------------------------------------
    # Formatting and Legend
    # ---------------------------------------------------------
    ax.set_xticks([0, pc, max_v])
    ax.set_xticklabels(['0', r'$p_c$', '4'], fontsize=14)
    ax.set_yticks([0, pr, max_v])
    ax.set_yticklabels(['0', r'$p_r$', '4'], fontsize=14)
    
    ax.set_xlabel(r'Willingness to pay for chocolate croissant ($v_c$)', fontsize=14)
    ax.set_ylabel(r'Willingness to pay for regular croissant ($v_r$)', fontsize=14)
    ax.set_title('Complete Customer Purchasing Behavior Map', fontsize=16, pad=20)
    
    # Create custom legend patches for Ex 4 Areas
    patch_none = mpatches.Patch(color=color_none, label='Ex 4 Area (i): Do Not Buy Anything')
    patch_reg = mpatches.Patch(color=color_reg, label='Ex 4 Area (ii): Buy Regular Croissant')
    patch_choc = mpatches.Patch(color=color_choc, label='Ex 4 Area (iii): Buy Chocolate Croissant')
    
    # Combine the custom patches with the indifference line legend
    handles, labels = ax.get_legend_handles_labels() 
    handles.extend([patch_none, patch_reg, patch_choc])
    
    ax.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=2, fontsize=12)
    
    # Clean up borders
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_xlim(0, max_v + 0.2)
    ax.set_ylim(0, max_v + 0.2)
    
    plt.tight_layout()
    plt.show()

# Run the function
plot_complete_assignment(pc=1.5, pr=2.5, max_v=4)